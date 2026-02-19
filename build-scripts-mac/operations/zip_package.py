"""
Zip operation: Create a zip archive of the Bidding Scenarios folder.

The zip file is placed at Bidding Scenarios/Bidding Scenarios.zip.
Only rebuilds if any file in the hierarchy is newer than the existing zip.

This operation is NOT included in OPERATIONS_ORDER — it must be invoked
explicitly (e.g., python3 pbs-pipeline-mac.py layout zip).
The scenario argument is ignored; the entire folder is always zipped.
"""
import os
import sys
import zipfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROJECT_ROOT

ZIP_NAME = "Bidding Scenarios.zip"


def run_zip(scenario: str, verbose: bool = True) -> bool:
    """
    Create a zip archive of the Bidding Scenarios folder.

    The scenario argument is ignored — the entire folder is always zipped.

    Args:
        scenario: Ignored (required by pipeline interface)
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Zipping Bidding Scenarios")

    bs_dir = os.path.join(PROJECT_ROOT, "Bidding Scenarios")
    if not os.path.isdir(bs_dir):
        if verbose:
            print("  Bidding Scenarios folder not found — skipping")
        return True

    zip_path = os.path.join(bs_dir, ZIP_NAME)

    # Collect all files (excluding the zip itself)
    files_to_zip = []
    for dirpath, _dirnames, filenames in os.walk(bs_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if full_path == zip_path:
                continue
            files_to_zip.append(full_path)

    if not files_to_zip:
        if verbose:
            print("  No files to zip")
        return True

    # Check if rebuild is needed: any file newer than the zip?
    if os.path.exists(zip_path):
        zip_mtime = os.path.getmtime(zip_path)
        newest = max(os.path.getmtime(f) for f in files_to_zip)
        if zip_mtime >= newest:
            if verbose:
                print("  Zip is up to date — skipping")
            return True

    # Build the zip
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for full_path in sorted(files_to_zip):
            # Archive name is relative to the parent of Bidding Scenarios,
            # so the zip extracts as "Bidding Scenarios/..."
            arc_name = os.path.relpath(full_path, os.path.dirname(bs_dir))
            zf.write(full_path, arc_name)
            count += 1

    if verbose:
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"  Created {ZIP_NAME}: {count} files, {size_mb:.1f} MB")

    return True


if __name__ == "__main__":
    print("Testing zip operation\n")
    success = run_zip("_")
    print(f"\nResult: {'Success' if success else 'Failed'}")
