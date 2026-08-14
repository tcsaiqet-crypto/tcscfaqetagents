"""ZIP and Document Intake Service."""

import os
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from src.config import config
from src.models.schemas import IntakeManifest, FileMetadata
from src.utils.security import validate_and_extract_zip, SecurityError
from src.utils.logger import logger


class ZipService:
    """Service for handling uploaded ZIP source code archives and supporting documents."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or config.get_extracted_source_dir()

    def process_zip_upload(self, upload_id: str, zip_path: Path, filename: str) -> IntakeManifest:
        """Extract and index uploaded ZIP archive safely."""
        logger.info(f"Processing ZIP archive upload '{filename}' with ID {upload_id}")
        
        extracted_dir = self.target_dir / upload_id
        file_metadatas, total_files, total_bytes = validate_and_extract_zip(zip_path, extracted_dir)

        doc_files: List[str] = []
        for file_meta in file_metadatas:
            if file_meta.extension in {".pdf", ".md", ".txt", ".docx", ".doc"}:
                doc_files.append(file_meta.rel_path)

        manifest = IntakeManifest(
            upload_id=upload_id,
            zip_filename=filename,
            extracted_path=str(extracted_dir),
            total_files=total_files,
            total_size_bytes=total_bytes,
            files=file_metadatas,
            doc_files=doc_files,
            created_at="2026-08-13T14:00:00Z"
        )
        return manifest

    def inspect_source_files(self, extracted_path: str) -> Dict[str, str]:
        """Read text content of source files for agent analysis."""
        base_path = Path(extracted_path)
        source_contents: Dict[str, str] = {}
        
        if not base_path.exists():
            return source_contents

        for root, _, files in os.walk(base_path):
            for file in files:
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(base_path))
                ext = file_path.suffix.lower()
                
                # Focus on relevant source and doc extensions
                if ext in {".html", ".js", ".jsx", ".ts", ".tsx", ".py", ".json", ".md", ".txt"}:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            source_contents[rel_path] = content[:10000]  # First 10k chars per file
                    except Exception as e:
                        logger.warning(f"Could not read source file {rel_path}: {e}")

        return source_contents
