"""Document and ZIP Upload Service managing run-specific uploads."""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from src.config import config
from src.utils.security import SecurityError
from src.utils.logger import logger


class UploadService:
    """Service handling document and single ZIP archive uploads per run."""

    ALLOWED_DOC_EXTENSIONS = {".pdf", ".md", ".txt", ".docx", ".doc"}
    MAX_DOC_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit per document

    def __init__(self, base_upload_dir: Optional[Path] = None):
        self.base_upload_dir = base_upload_dir or Path("uploads")
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    def get_run_upload_dir(self, run_id: str) -> Path:
        """Get or create run-specific upload directory."""
        run_dir = self.base_upload_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_uploaded_document(self, run_id: str, filename: str, content_bytes: bytes) -> Path:
        """Validate and save a supporting business/technical document."""
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_DOC_EXTENSIONS:
            raise SecurityError(f"File type '{ext}' is not supported for document upload. Allowed: {self.ALLOWED_DOC_EXTENSIONS}")

        if len(content_bytes) > self.MAX_DOC_SIZE_BYTES:
            raise SecurityError(f"Document '{filename}' size ({len(content_bytes)} bytes) exceeds limit of {self.MAX_DOC_SIZE_BYTES} bytes")

        run_dir = self.get_run_upload_dir(run_id) / "documents"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = run_dir / filename
        with open(target_path, "wb") as f:
            f.write(content_bytes)

        logger.info(f"Saved document '{filename}' for run '{run_id}'")
        return target_path

    def validate_zip_upload(self, zip_filename: str, content_bytes: bytes) -> None:
        """Validate ZIP upload parameters (single archive, size limit)."""
        ext = Path(zip_filename).suffix.lower()
        if ext != ".zip":
            raise SecurityError(f"Only .zip format is accepted for source code upload. Received: '{ext}'")

        max_zip_bytes = 25 * 1024 * 1024  # 25 MB max upload archive size
        if len(content_bytes) > max_zip_bytes:
            raise SecurityError(f"ZIP archive size ({len(content_bytes)} bytes) exceeds maximum upload limit of {max_zip_bytes} bytes")
