"""Unit tests for security and safe ZIP extraction module."""

import io
import zipfile
import pytest
from pathlib import Path
from src.config import config
from src.utils.security import (
    is_safe_path,
    validate_and_extract_zip,
    sanitize_log_message,
    SecurityError,
)


def test_is_safe_path(tmp_path: Path) -> None:
    base_dir = tmp_path / "safe"
    base_dir.mkdir()
    
    inside_path = base_dir / "subdir" / "file.txt"
    assert is_safe_path(base_dir, inside_path) is True
    
    outside_path = base_dir / ".." / "outside.txt"
    assert is_safe_path(base_dir, outside_path) is False


def test_valid_zip_extraction(tmp_path: Path) -> None:
    zip_path = tmp_path / "test.zip"
    extract_dir = tmp_path / "output"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("component.js", "console.log('hello');")
        zf.writestr("docs/readme.md", "# Test Project")
        
    extracted_files, count, total_bytes = validate_and_extract_zip(zip_path, extract_dir)
    
    assert count == 2
    assert total_bytes > 0
    assert len(extracted_files) == 2
    assert (extract_dir / "component.js").exists()
    assert (extract_dir / "docs" / "readme.md").exists()


def test_zip_exceeding_file_count_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "max_zip_file_count", 2)
    zip_path = tmp_path / "too_many.zip"
    extract_dir = tmp_path / "output"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("f1.txt", "1")
        zf.writestr("f2.txt", "2")
        zf.writestr("f3.txt", "3")
        
    with pytest.raises(SecurityError, match="exceeding maximum limit"):
        validate_and_extract_zip(zip_path, extract_dir)


def test_zip_forbidden_extension(tmp_path: Path) -> None:
    zip_path = tmp_path / "malicious.zip"
    extract_dir = tmp_path / "output"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("payload.exe", "binary payload")
        
    with pytest.raises(SecurityError, match="Forbidden file extension"):
        validate_and_extract_zip(zip_path, extract_dir)


def test_zip_slip_traversal_blocked(tmp_path: Path) -> None:
    zip_path = tmp_path / "zip_slip.zip"
    extract_dir = tmp_path / "output"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../traversal.py", "print('hacked')")
        
    with pytest.raises(SecurityError, match="Zip Slip path traversal detected"):
        validate_and_extract_zip(zip_path, extract_dir)


def test_sanitize_log_message() -> None:
    raw_log = "User connected with api_key: 'sk-1234567890abcdef1234567890abcdef' and password=SuperSecretPassword123"
    sanitized = sanitize_log_message(raw_log)
    assert "SuperSecretPassword123" not in sanitized
    assert "sk-1234567890abcdef1234567890abcdef" not in sanitized
    assert "***REDACTED***" in sanitized
