"""Unit tests for UploadService and safe upload validation."""

import pytest
from pathlib import Path
from services.upload_service import UploadService
from services.source_inventory import SourceInventoryService
from schemas.contracts import IntakeManifest, FileMetadata
from src.utils.security import SecurityError


def test_valid_document_upload(tmp_path: Path) -> None:
    service = UploadService(base_upload_dir=tmp_path)
    run_id = "RUN-TEST-001"
    content = b"# CFA Digital Journey Requirements\n\n1. Applicants must authenticate..."
    
    saved_path = service.save_uploaded_document(run_id, "requirements.md", content)
    
    assert saved_path.exists()
    assert saved_path.parent.name == "documents"
    assert saved_path.name == "requirements.md"
    assert saved_path.read_bytes() == content


def test_unsupported_document_extension(tmp_path: Path) -> None:
    service = UploadService(base_upload_dir=tmp_path)
    run_id = "RUN-TEST-002"
    
    with pytest.raises(SecurityError, match="not supported for document upload"):
        service.save_uploaded_document(run_id, "malicious_script.exe", b"binary executable content")


def test_oversized_document_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service = UploadService(base_upload_dir=tmp_path)
    monkeypatch.setattr(service, "MAX_DOC_SIZE_BYTES", 100)
    
    with pytest.raises(SecurityError, match="exceeds limit"):
        service.save_uploaded_document("RUN-TEST-003", "big_doc.pdf", b"x" * 500)


def test_zip_upload_validation(tmp_path: Path) -> None:
    service = UploadService(base_upload_dir=tmp_path)
    
    # Non-zip extension rejected
    with pytest.raises(SecurityError, match="Only .zip format is accepted"):
        service.validate_zip_upload("codebase.tar.gz", b"content")


def test_source_inventory_summary() -> None:
    inventory_service = SourceInventoryService()
    manifest = IntakeManifest(
        upload_id="upl_999",
        zip_filename="cfa_source.zip",
        extracted_path="/tmp/extracted",
        total_files=3,
        total_size_bytes=1500,
        files=[
            FileMetadata(rel_path="Login.tsx", size_bytes=500, extension=".tsx"),
            FileMetadata(rel_path="styles.css", size_bytes=400, extension=".css"),
            FileMetadata(rel_path="reqs.md", size_bytes=600, extension=".md")
        ],
        doc_files=["reqs.md"],
        created_at="2026-08-13T14:30:00Z"
    )
    
    summary = inventory_service.summarize_inventory(manifest)
    assert summary["total_files"] == 3
    assert summary["category_counts"]["React / TypeScript Component"] == 1
    assert summary["category_counts"]["CSS Stylesheet"] == 1
    assert summary["category_counts"]["Markdown Requirement Doc"] == 1
