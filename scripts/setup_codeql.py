import os
import sys
import time
import subprocess
from pathlib import Path
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
CODEQL_BUNDLE_URL = "https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.23.2/codeql-bundle-win64.tar.gz"
ARCHIVE_PATH = ROOT_DIR / "codeql-bundle-win64.tar.gz"
TARGET_CODEQL_DIR = ROOT_DIR / "codeql"

def download_with_progress(url, dest_path):
    print(f"Downloading CodeQL Bundle from:\n  {url}")
    print(f"Saving to:\n  {dest_path}")
    
    start_time = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB
        last_print = 0
        
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            
            # Print progress every 50MB or at completion
            if downloaded - last_print >= 50 * 1024 * 1024 or downloaded == total_size:
                last_print = downloaded
                pct = (downloaded / total_size * 100) if total_size else 0
                elapsed = time.time() - start_time
                speed = (downloaded / 1024 / 1024) / elapsed if elapsed > 0 else 0
                print(f"  Progress: {downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB ({pct:.1f}%) - Speed: {speed:.1f} MB/s")

    print(f"Download completed in {time.time() - start_time:.1f}s.")

def extract_archive(archive_path, target_root):
    print("Extracting archive using tar.exe...")
    start_time = time.time()
    cmd = ["tar.exe", "-xzf", str(archive_path), "-C", str(target_root)]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"tar.exe failed with exit code {res.returncode}, falling back to Python tarfile...")
        import tarfile
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(target_root)
    print(f"Extraction completed in {time.time() - start_time:.1f}s.")

def main():
    if TARGET_CODEQL_DIR.exists() and (TARGET_CODEQL_DIR / "codeql.exe").exists():
        print(f"CodeQL directory already exists at {TARGET_CODEQL_DIR}.")
        if (TARGET_CODEQL_DIR / "qlpacks").exists():
            print("qlpacks directory found. Setup is already complete.")
            return

    try:
        download_with_progress(CODEQL_BUNDLE_URL, ARCHIVE_PATH)
        extract_archive(ARCHIVE_PATH, ROOT_DIR)
    finally:
        if ARCHIVE_PATH.exists():
            print("Cleaning up downloaded archive...")
            try:
                ARCHIVE_PATH.unlink()
            except Exception as e:
                print(f"Could not remove archive: {e}")

    codeql_exe = TARGET_CODEQL_DIR / "codeql.exe"
    qlpacks_dir = TARGET_CODEQL_DIR / "qlpacks"
    
    if codeql_exe.exists() and qlpacks_dir.exists():
        print("\n" + "=" * 60)
        print("  CODEQL ACTION BUNDLE SETUP SUCCESSFUL!")
        print(f"  Binary:   {codeql_exe}")
        print(f"  QL Packs: {qlpacks_dir}")
        print("=" * 60)
        
        # Test command
        res = subprocess.run([str(codeql_exe), "version"], capture_output=True, text=True)
        print(res.stdout)
    else:
        print("\nERROR: Verification failed after extraction. Please check directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
