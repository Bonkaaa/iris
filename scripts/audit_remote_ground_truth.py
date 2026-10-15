#!/usr/bin/env python3
"""
Audit all 25 projects in fix_info.csv against their buggy_commit_id from project_info.csv.
Uses GitHub raw URLs and GitHub API (or local sources if available) to verify:
1. Does the file exist at that exact path in the buggy commit?
2. Does the class exist?
3. Does the method exist?
4. If file is 404, queries GitHub tree to find the actual location in the repo.
"""

import csv
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_INFO_CSV = ROOT_DIR / "z_data" / "project_info.csv"
FIX_INFO_CSV = ROOT_DIR / "z_data" / "fix_info.csv"
SOURCES_DIR = ROOT_DIR / "z_data" / "project-sources"

def load_data():
    projects = {}
    with open(PROJECT_INFO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            slug = r["project_slug"]
            projects[slug] = r

    ground_truth = []
    with open(FIX_INFO_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            ground_truth.append(r)

    return projects, ground_truth

def get_file_content(slug, proj_info, rel_path, commit_id):
    # 1. First check local project-sources
    local_path = SOURCES_DIR / slug / rel_path
    if local_path.exists():
        return local_path.read_text(encoding="utf-8", errors="ignore"), "LOCAL"

    # 2. Try GitHub raw URL
    user = proj_info["github_username"]
    repo = proj_info["github_repository_name"]
    raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{commit_id}/{rel_path}"
    
    req = urllib.request.Request(raw_url, headers={"User-Agent": "IRIS-Auditor"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return content, "GITHUB_RAW"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "NOT_FOUND_404"
        return None, f"HTTP_ERR_{e.code}"
    except Exception as e:
        return None, f"ERR_{str(e)[:30]}"

def find_file_in_tree(proj_info, commit_id, filename):
    user = proj_info["github_username"]
    repo = proj_info["github_repository_name"]
    tree_url = f"https://api.github.com/repos/{user}/{repo}/git/trees/{commit_id}?recursive=1"
    req = urllib.request.Request(tree_url, headers={"User-Agent": "IRIS-Auditor"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            paths = [item["path"] for item in data.get("tree", []) if item["path"].endswith("/" + filename) or item["path"] == filename]
            return paths
    except Exception as e:
        return []

def main():
    projects, ground_truth = load_data()
    print("=" * 100)
    print(f"AUDITING ALL {len(ground_truth)} PROJECTS AGAINST BUGGY (VIC) COMMITS")
    print("=" * 100)

    results = []

    for idx, gt in enumerate(ground_truth, 1):
        slug = gt["project_slug"]
        rel_path = gt["file"]
        target_class = gt["class"]
        target_method = gt["method"]

        pinfo = projects.get(slug)
        if not pinfo:
            print(f"[{idx:2d}/25] {slug[:30]:<30} | NOT IN project_info.csv")
            continue

        commit = pinfo["buggy_commit_id"]
        content, source = get_file_content(slug, pinfo, rel_path, commit)

        if content is None:
            # File not found at specified path, try tree search
            fname = Path(rel_path).name
            tree_matches = find_file_in_tree(pinfo, commit, fname)
            results.append({
                "idx": idx,
                "slug": slug,
                "file": rel_path,
                "status": "NOT_FOUND",
                "source": source,
                "tree_matches": tree_matches,
                "class_ok": False,
                "method_ok": False,
                "class": target_class,
                "method": target_method
            })
            print(f"[{idx:2d}/25] {slug[:32]:<32} | FILE NOT FOUND ({source}) -> Tree matches: {tree_matches}")
        else:
            class_ok = bool(re.search(r'\b(class|interface|enum)\s+' + re.escape(target_class) + r'\b', content))
            method_ok = bool(re.search(r'\b' + re.escape(target_method) + r'\s*\(', content))
            flag = "OK" if (class_ok and method_ok) else "MISMATCH"
            results.append({
                "idx": idx,
                "slug": slug,
                "file": rel_path,
                "status": flag,
                "source": source,
                "class_ok": class_ok,
                "method_ok": method_ok,
                "class": target_class,
                "method": target_method
            })
            print(f"[{idx:2d}/25] {slug[:32]:<32} | [{flag:<8}] Class: {str(class_ok):<5} | Method: {str(method_ok):<5} | Source: {source}")

    print("=" * 100)
    mismatches = [r for r in results if r["status"] != "OK"]
    print(f"AUDIT SUMMARY: {len(results) - len(mismatches)}/{len(results)} MATCHED 100%, {len(mismatches)} ISSUES FLAGGED")
    if mismatches:
        print("\nDetails of issues:")
        for m in mismatches:
            print(f"- {m['slug']}: File: {m['file']} -> {m['status']}")
            if not m["class_ok"]: print(f"    Class '{m['class']}' not found")
            if not m["method_ok"]: print(f"    Method '{m['method']}' not found")
            if m.get("tree_matches"): print(f"    Actual candidates in repo: {m['tree_matches']}")

if __name__ == "__main__":
    main()
