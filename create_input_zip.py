"""Helper script to package the input folder with 5 defective programs into a ZIP file."""

import os
import zipfile
from pathlib import Path

def create_zip_archive():
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    zip_path = base_dir / "input.zip"
    
    if not input_dir.exists():
        print(f"[ERROR] Input directory does not exist at {input_dir}")
        return False
        
    print(f"Creating ZIP archive from '{input_dir}' -> '{zip_path}'...")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                full_path = Path(root) / file
                # Store relative path inside the zip file
                rel_path = full_path.relative_to(base_dir)
                zip_file.write(full_path, arcname=rel_path)
                print(f"  + Added: {rel_path}")

    print(f"[SUCCESS] ZIP archive created successfully at: {zip_path.resolve()}")
    print(f"Size: {zip_path.stat().st_size} bytes")

    # Also list archive contents for verification
    with zipfile.ZipFile(zip_path, "r") as z:
        print("\nZIP Archive Contents:")
        for info in z.infolist():
            print(f"  - {info.filename} ({info.file_size} bytes)")

    return True

if __name__ == "__main__":
    create_zip_archive()
