"""Data Processor - Defect: Resource leak (unclosed files) & swallowed exceptions."""

import json
import os
from typing import Dict, Any


def load_applicant_batch(file_path: str) -> Dict[str, Any]:
    """Loads applicant json file from filesystem."""
    # DEFECT 1 (Resource Leak): File is opened using open() without context manager 'with' or try/finally.
    # If JSON parsing fails or exception occurs, the file descriptor remains open indefinitely.
    file_handle = open(file_path, "r", encoding="utf-8")
    data = json.load(file_handle)
    # Missing file_handle.close()
    return data


def process_and_save_report(output_path: str, records: list) -> bool:
    """Processes record batch and writes output file."""
    try:
        f = open(output_path, "w", encoding="utf-8")
        for item in records:
            # DEFECT 2 (Exception Swallowing): Broad exception catch that silently suppresses errors
            try:
                formatted = f"ID:{item['id']} - Name:{item['name'].upper()}\n"
                f.write(formatted)
            except Exception:
                # Silently ignoring missing keys or bad data without logging or raising
                pass
        f.close()
        return True
    except Exception as e:
        # DEFECT 3 (Silent Fallback): Swallows top-level file errors and returns True anyway
        return True
