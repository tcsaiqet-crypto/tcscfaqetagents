"""Security & Safe ZIP Extraction Utilities."""

import os
import re
import zipfile
from pathlib import Path
from typing import List, Tuple
from src.config import config
from src.models.schemas import FileMetadata


class SecurityError(ValueError):
    """Custom exception raised when security validation fails."""
    pass


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Validate that target_path is within base_dir (Zip Slip protection)."""
    resolved_base = base_dir.resolve()
    resolved_target = target_path.resolve()
    try:
        resolved_target.relative_to(resolved_base)
        return True
    except ValueError:
        return False


def validate_and_extract_zip(zip_path: Path, target_dir: Path) -> Tuple[List[FileMetadata], int, int]:
    """
    Safely extract ZIP archive enforcing limits and path traversal checks.
    
    Returns:
        Tuple[List[FileMetadata], total_file_count, total_bytes_extracted]
    """
    if not zip_path.exists():
        raise SecurityError(f"ZIP file does not exist at {zip_path}")
        
    if not zipfile.is_zipfile(zip_path):
        raise SecurityError(f"Provided file {zip_path.name} is not a valid ZIP archive")

    target_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_files: List[FileMetadata] = []
    total_files = 0
    total_bytes = 0

    with zipfile.ZipFile(zip_path, 'r') as zf:
        infolist = zf.infolist()
        
        # 1. Limit Check: Total file count
        if len(infolist) > config.max_zip_file_count:
            raise SecurityError(
                f"ZIP contains {len(infolist)} files, exceeding maximum limit of {config.max_zip_file_count}"
            )

        for member in infolist:
            # Ignore directory entries for size/limit checks
            if member.is_dir():
                continue

            # 2. Limit Check: Single file size
            if member.file_size > config.max_single_file_bytes:
                raise SecurityError(
                    f"File {member.filename} size ({member.file_size} bytes) exceeds limit of {config.max_single_file_bytes} bytes"
                )

            # 3. Extension check
            ext = Path(member.filename).suffix.lower()
            if ext in config.forbidden_extensions:
                raise SecurityError(
                    f"Forbidden file extension '{ext}' detected in member '{member.filename}'"
                )

            total_files += 1
            total_bytes += member.file_size

            # 4. Limit Check: Cumulative total bytes
            if total_bytes > config.max_zip_total_bytes:
                raise SecurityError(
                    f"Total uncompressed ZIP size exceeds maximum limit of {config.max_zip_total_bytes} bytes"
                )

            # 5. Zip Slip Path Traversal Check
            dest_path = target_dir / member.filename
            if not is_safe_path(target_dir, dest_path):
                raise SecurityError(
                    f"Potential Zip Slip path traversal detected: '{member.filename}'"
                )

        # Extraction loop after passing all validations
        for member in infolist:
            if member.is_dir():
                continue
            dest_path = target_dir / member.filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with zf.open(member) as source, open(dest_path, "wb") as target:
                target.write(source.read())

            ext = dest_path.suffix.lower()
            extracted_files.append(
                FileMetadata(
                    rel_path=member.filename,
                    size_bytes=dest_path.stat().st_size,
                    extension=ext,
                    is_binary=ext in {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".ico", ".woff", ".ttf"}
                )
            )

    return extracted_files, total_files, total_bytes


def sanitize_log_message(msg: str) -> str:
    """Mask credentials and sensitive strings in log messages."""
    # Mask common key-value pattern secrets (tokens, API keys, passwords)
    patterns = [
        (r'(?i)(api[_-]?key|password|secret|token|bearer)\s*[:=]\s*["\']?([^"\'\s]+)["\']?', r'\1=***REDACTED***'),
        (r'sk-[a-zA-Z0-9]{32,}', 'sk-***REDACTED***')
    ]
    sanitized = msg
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)
    return sanitized
