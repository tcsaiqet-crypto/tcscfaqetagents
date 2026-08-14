"""Source Inventory & Language Summary Service."""

import os
from pathlib import Path
from typing import Dict, List, Any
from schemas.contracts import IntakeManifest, FileMetadata


class SourceInventoryService:
    """Indexes extracted source tree, categorizes files, and summarizes language statistics."""

    CATEGORY_MAP = {
        ".ts": "TypeScript Source",
        ".tsx": "React / TypeScript Component",
        ".js": "JavaScript Source",
        ".jsx": "React / JavaScript Component",
        ".py": "Python Source",
        ".html": "HTML View Template",
        ".css": "CSS Stylesheet",
        ".json": "JSON Data / Config",
        ".md": "Markdown Requirement Doc",
        ".txt": "Plain Text Document",
        ".pdf": "PDF Specification Doc"
    }

    def summarize_inventory(self, manifest: IntakeManifest) -> Dict[str, Any]:
        """Compute category file counts and language distribution."""
        category_counts: Dict[str, int] = {}
        extension_counts: Dict[str, int] = {}
        total_size = manifest.total_size_bytes

        for file in manifest.files:
            ext = file.extension.lower()
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
            
            cat = self.CATEGORY_MAP.get(ext, "Other Asset")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "upload_id": manifest.upload_id,
            "total_files": manifest.total_files,
            "total_size_bytes": total_size,
            "category_counts": category_counts,
            "extension_counts": extension_counts,
            "document_files": manifest.doc_files
        }
