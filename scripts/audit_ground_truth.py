#!/usr/bin/env python3
"""
Audit Ground Truth (fix_info.csv) against project-sources at VIC commits.
Checks:
1. Does the target file exist at the specified relative path?
2. If not, does the file exist at an alternative path in the repo?
3. Does the enclosing class exist in that file?
4. Does the enclosing method exist in that file?
"""

import os
import csv
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FIX_INFO_CSV = ROOT_DIR / "z_data" / "fix_info.csv"
SOURCES_DIR = ROOT_DIR / "z_data" / "project-sources"

def audit():
    if not FIX_INFO_CSV.exists():
        print(f"Error: {FIX_INFO_CSV} not found!")
        return

    with open(FIX_INFO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total projects in fix_info.csv: {len(rows)}")
    print("=" * 80)

    checked = 0
    issues = 0

    for idx, r in enumerate(rows, 1):
        slug = r["project_slug"]
        rel_file = r["file"]
        target_class = r["class"]
        target_method = r["method"]

        proj_dir = SOURCES_DIR / slug
        if not proj_dir.exists():
            print(f"[{idx:2d}/25] {slug[:35]:<35} | SOURCE NOT DOWNLOADED YET")
            continue

        checked += 1
        full_path = proj_dir / rel_file
        file_status = "OK"
        actual_rel_file = rel_file

        if not full_path.exists():
            # Try to locate by filename
            fname = Path(rel_file).name
            matches = list(proj_dir.rglob(fname))
            if matches:
                actual_rel_file = str(matches[0].relative_to(proj_dir)).replace("\\", "/")
                full_path = matches[0]
                file_status = f"PATH MISMATCH -> Found at: {actual_rel_file}"
                issues += 1
            else:
                file_status = "FILE NOT FOUND"
                issues += 1
                print(f"[{idx:2d}/25] {slug[:35]:<35} | File: {file_status}")
                continue

        # Check content for class and method
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        class_found = bool(re.search(r'\b(class|interface|enum)\s+' + re.escape(target_class) + r'\b', content))
        method_found = bool(re.search(r'\b' + re.escape(target_method) + r'\s*\(', content))

        issue_flag = ""
        if not class_found or not method_found or file_status != "OK":
            issues += 1
            issue_flag = " [!] NEEDS ALIGNMENT"

        print(f"[{idx:2d}/25] {slug[:35]:<35} | File: {file_status} | Class: {class_found} | Method: {method_found}{issue_flag}")

    print("=" * 80)
    print(f"Audit completed: {checked}/{len(rows)} projects checked locally, {issues} potential discrepancies flagged.")

if __name__ == "__main__":
    audit()
