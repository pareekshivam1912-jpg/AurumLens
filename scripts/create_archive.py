#!/usr/bin/env python3
"""
AurumLens — Project Archive Packager.

Packages the complete project into a clean, portable ZIP archive,
excluding large ephemeral build artifacts:
  - .git/
  - node_modules/
  - .next/
  - __pycache__/
  - .pytest_cache/
  - *.pyc / *.pyo
"""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

# Fix Windows stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = PROJECT_ROOT / "AurumLens_v2_Complete.zip"

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

EXCLUDED_FILES = {
    "AurumLens_v2_Complete.zip",
    ".DS_Store",
    "Thumbs.db",
}

EXCLUDED_EXTS = {
    ".pyc",
    ".pyo",
    ".log",
}


def should_exclude(path: Path) -> bool:
    # Check directory parts
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
    if path.name in EXCLUDED_FILES:
        return True
    if path.suffix.lower() in EXCLUDED_EXTS:
        return True
    return False


def create_archive() -> None:
    print(f"[*] Packaging AurumLens project into: {OUTPUT_ZIP.name}")
    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                file_path = Path(root) / file
                if should_exclude(file_path):
                    continue

                rel_path = file_path.relative_to(PROJECT_ROOT)
                zipf.write(file_path, arcname=str(rel_path))
                file_count += 1
                total_uncompressed_bytes += file_path.stat().st_size

    zip_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    raw_size_mb = total_uncompressed_bytes / (1024 * 1024)

    print(f"[+] Archive created successfully!")
    print(f"    - Files packaged: {file_count}")
    print(f"    - Raw uncompressed size: {raw_size_mb:.2f} MB")
    print(f"    - Compressed ZIP size: {zip_size_mb:.2f} MB")
    print(f"    - Destination: {OUTPUT_ZIP}")


if __name__ == "__main__":
    create_archive()
