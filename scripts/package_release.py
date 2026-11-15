"""AI Panel Studio — Clean Source Distribution Packager.

Packages the entire project into a standalone zip file excluding:
- .git repository
- Python virtual environments (.venv, venv)
- Node modules (node_modules)
- Sensitive environment files (.env)
- Local SQLite database files (*.db, *.db-wal, *.db-shm)
- Python cache files (__pycache__, *.pyc, .pytest_cache, .ruff_cache)
- Temporary build outputs (dist)
"""

import os
import sys
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_ZIP_NAME = "ai-panel-studio-release.zip"
OUTPUT_ZIP_PATH = os.path.join(PROJECT_ROOT, OUTPUT_ZIP_NAME)

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
}

EXCLUDED_FILE_NAMES = {
    ".env",
    OUTPUT_ZIP_NAME,
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".db",
    ".db-wal",
    ".db-shm",
    ".log",
}


def should_exclude(rel_path: str) -> bool:
    """Determine whether a file or directory should be excluded from package."""
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDED_DIR_NAMES:
            return True

    file_name = parts[-1]
    if file_name in EXCLUDED_FILE_NAMES:
        return True

    _, ext = os.path.splitext(file_name)
    if ext.lower() in EXCLUDED_EXTENSIONS:
        return True

    return False


def create_release_package() -> None:
    """Create the clean zip package."""
    print(f"📦 Packaging AI Panel Studio from {PROJECT_ROOT}...")

    total_files = 0
    total_size = 0

    with zipfile.ZipFile(OUTPUT_ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Exclude directory in-place to prevent descending into it
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]

            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, PROJECT_ROOT)

                if should_exclude(rel_path):
                    continue

                zip_file.write(abs_path, rel_path)
                total_files += 1
                total_size += os.path.getsize(abs_path)

    zip_size_mb = os.path.getsize(OUTPUT_ZIP_PATH) / (1024 * 1024)
    print(f"✅ Successfully created release package: {OUTPUT_ZIP_NAME}")
    print(f"   Files packaged: {total_files}")
    print(f"   Uncompressed size: {total_size / (1024 * 1024):.2f} MB")
    print(f"   Package size: {zip_size_mb:.2f} MB")
    print(f"   Location: {OUTPUT_ZIP_PATH}")


if __name__ == "__main__":
    create_release_package()
