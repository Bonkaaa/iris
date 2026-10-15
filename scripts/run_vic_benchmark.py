#!/usr/bin/env python3
"""
Batch Runner for VIC Benchmark on IRIS
Executes fetch, build CodeQL DB, extract package names, and run IRIS analysis
for all projects in project_info.csv.
"""

import os
import sys
import csv
import argparse
import subprocess
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import DATA_DIR, CODEQL_DB_PATH, PACKAGE_MODULES_PATH, PROJECT_SOURCE_CODE_DIR, OUTPUT_DIR

# Mapping from CWE-ID to IRIS Query name
CWE_TO_QUERY = {
    "CWE-022": "cwe-022wLLM",
    "CWE-078": "cwe-078wLLM",
    "CWE-079": "cwe-079wLLM",
    "CWE-094": "cwe-094wLLM",
}

def load_projects(csv_path):
    projects = []
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        sys.exit(1)
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 4 and row[1].strip():
                slug = row[1].strip()
                cve_id = row[2].strip()
                cwe_id = row[3].strip()
                projects.append({
                    "slug": slug,
                    "cve_id": cve_id,
                    "cwe_id": cwe_id,
                    "query": CWE_TO_QUERY.get(cwe_id, f"{cwe_id.lower().replace('-', '')}wLLM")
                })
    return projects

def run_cmd(cmd, step_name):
    print(f"  [EXEC] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if result.returncode != 0:
        print(f"  [ERROR] {step_name} failed with exit code {result.returncode}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Run VIC Benchmark on IRIS for all datapoints")
    parser.add_argument("--llm", default="gemini-3.5-flash-lite", help="LLM to use (e.g., gemini-3.5-flash-lite, gemini-1.5-flash, gemini-1.5-pro, gpt-4)")
    parser.add_argument("--run-id", default="vic_run", help="Run ID for storing outputs")
    parser.add_argument("--num-threads", type=int, default=4, help="Number of concurrent threads for LLM calls (use 2-4 for Gemini Free Tier)")
    parser.add_argument("--filter", nargs="+", help="Filter specific project slugs or substrings")
    parser.add_argument("--exclude", nargs="+", default=[], help="Exclude specific project slugs or substrings (e.g., --exclude flink)")
    parser.add_argument("--resume", action="store_true", help="Resume run: skip execution if results.json already exists in output directory")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip git clone/checkout step")
    parser.add_argument("--skip-build-db", action="store_true", help="Skip CodeQL DB build step")
    parser.add_argument("--skip-packages", action="store_true", help="Skip internal package extraction step")
    parser.add_argument("--skip-iris", action="store_true", help="Skip IRIS analysis step")
    args = parser.parse_args()

    project_info_csv = os.path.join(DATA_DIR, "project_info.csv")
    projects = load_projects(project_info_csv)

    if args.filter:
        projects = [p for p in projects if any(f in p["slug"] for f in args.filter)]
    if args.exclude:
        projects = [p for p in projects if not any(e in p["slug"] for e in args.exclude)]

    print("=" * 70)
    print(f"  STARTING VIC BENCHMARK ({len(projects)} PROJECTS)")
    print(f"  Data Directory: {DATA_DIR}")
    print(f"  LLM Model:      {args.llm}")
    print(f"  Run ID:         {args.run_id}")
    if args.exclude:
        print(f"  Excluded:       {', '.join(args.exclude)}")
    print("=" * 70)

    summary = []

    for idx, p in enumerate(projects, 1):
        slug = p["slug"]
        query = p["query"]
        print(f"\n[{idx}/{len(projects)}] Processing {slug} ({query})...")

        # Check if already completed when --resume is active
        res_file = Path(OUTPUT_DIR) / slug / args.run_id / f"{query}-final" / "results.json"
        if args.resume and res_file.exists():
            print(f"-> [RESUME] Skipping {slug}, final results already exist at {res_file}")
            recall_method = False
            time_sec = 0.0
            tokens = 0
            try:
                import json
                with open(res_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                recall_method = data.get("posthoc_filter_result", {}).get("recall_method", False)
                time_sec = data.get("execution_time_seconds", 0.0)
                tokens = data.get("token_usage", {}).get("total_tokens", 0)
            except Exception:
                pass
            summary.append({
                "slug": slug,
                "cwe": p["cwe_id"],
                "status": "CACHED",
                "recall_method": recall_method,
                "time_sec": time_sec,
                "tokens": tokens
            })
            continue
        
        # Step 1: Fetch project
        source_dir = Path(PROJECT_SOURCE_CODE_DIR) / slug
        if not args.skip_fetch:
            if not source_dir.exists():
                print(f"-> Step 1/4: Fetching {slug}...")
                ok = run_cmd([sys.executable, "scripts/fetch_one.py", slug], "Fetch")
                if not ok:
                    summary.append({
                        "slug": slug,
                        "cwe": p["cwe_id"],
                        "status": "FAILED (Fetch)",
                        "recall_method": False,
                        "time_sec": 0,
                        "tokens": 0
                    })
                    continue
            else:
                print(f"-> Step 1/4: Project sources already exist at {source_dir}, skipping fetch.")
        
        # Step 2: Build CodeQL DB
        db_dir = Path(CODEQL_DB_PATH) / slug
        if not args.skip_build_db:
            if not (db_dir / "db-java").exists():
                print(f"-> Step 2/4: Building CodeQL DB for {slug}...")
                ok = run_cmd([sys.executable, "scripts/build_codeql_dbs.py", "--project", slug], "Build CodeQL DB")
                if not ok:
                    summary.append({
                        "slug": slug,
                        "cwe": p["cwe_id"],
                        "status": "FAILED (Build DB)",
                        "recall_method": False,
                        "time_sec": 0,
                        "tokens": 0
                    })
                    continue
            else:
                print(f"-> Step 2/4: Valid CodeQL DB already exists at {db_dir}, skipping.")

        # Step 3: Extract Packages
        pkg_file = Path(PACKAGE_MODULES_PATH) / f"{slug}.txt"
        if not args.skip_packages:
            if not pkg_file.exists():
                print(f"-> Step 3/4: Extracting internal packages for {slug}...")
                ok = run_cmd([sys.executable, "scripts/get_packages_codeql.py", slug], "Extract Packages")
                if not ok:
                    print(f"  [WARN] Failed to extract package names automatically. Checking if file exists...")
            else:
                print(f"-> Step 3/4: Package file already exists at {pkg_file}, skipping.")

        # Step 4: Run IRIS Analysis
        if not args.skip_iris:
            print(f"-> Step 4/4: Running IRIS Analysis with {args.llm}...")
            ok = run_cmd([
                sys.executable, "src/iris.py", slug,
                "--query", query,
                "--llm", args.llm,
                "--run-id", args.run_id,
                "--num-threads", str(args.num_threads)
            ], "IRIS Analysis")
            if not ok:
                summary.append({
                    "slug": slug,
                    "cwe": p["cwe_id"],
                    "status": "FAILED (IRIS)",
                    "recall_method": False,
                    "time_sec": 0,
                    "tokens": 0
                })
                continue

        # Collect metrics from results.json if available
        res_file = Path(OUTPUT_DIR) / slug / args.run_id / f"{query}-final" / "results.json"
        recall_method = False
        time_sec = 0.0
        tokens = 0

        if res_file.exists():
            try:
                import json
                with open(res_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                recall_method = data.get("posthoc_filter_result", {}).get("recall_method", False)
                time_sec = data.get("execution_time_seconds", 0.0)
                tokens = data.get("token_usage", {}).get("total_tokens", 0)
            except Exception:
                pass

        summary.append({
            "slug": slug,
            "cwe": p["cwe_id"],
            "status": "SUCCESS",
            "recall_method": recall_method,
            "time_sec": time_sec,
            "tokens": tokens
        })

    # Print comprehensive summary table
    print("\n" + "=" * 105)
    print("                                      VIC BENCHMARK SUMMARY REPORT")
    print("=" * 105)
    header = f"| {'Project Slug':<55} | {'CWE':<7} | {'Status':<9} | {'Recall@M':<8} | {'Time (s)':<9} | {'Tokens':<9} |"
    print(header)
    print("|" + "-" * 57 + "|" + "-" * 9 + "|" + "-" * 11 + "|" + "-" * 10 + "|" + "-" * 11 + "|" + "-" * 11 + "|")

    total_time = 0.0
    total_tokens = 0
    total_tp = 0
    total_success = 0

    for item in summary:
        time_str = f"{item['time_sec']:.1f}s" if item['time_sec'] > 0 else "N/A"
        tok_str = f"{item['tokens']:,}" if item['tokens'] > 0 else "N/A"
        rec_str = "True" if item['recall_method'] else "False"
        print(f"| {item['slug']:<55} | {item['cwe']:<7} | {item['status']:<9} | {rec_str:<8} | {time_str:<9} | {tok_str:<9} |")
        
        if item["status"] == "SUCCESS":
            total_success += 1
            total_time += item["time_sec"]
            total_tokens += item["tokens"]
            if item["recall_method"]:
                total_tp += 1

    print("=" * 105)
    total_str = f"  Processed: {len(summary)} | Success: {total_success} | Recall@Method True: {total_tp}/{len(summary)} | Total Time: {total_time:.1f}s ({total_time/60:.1f}m) | Total Tokens: {total_tokens:,}"
    print(total_str)
    print("=" * 105)

    # Dump overall summary JSON
    summary_path = Path(OUTPUT_DIR) / f"benchmark_summary_{args.run_id}.json"
    try:
        import json
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "run_id": args.run_id,
                "llm": args.llm,
                "total_projects": len(summary),
                "successful_projects": total_success,
                "recall_method_count": total_tp,
                "total_execution_time_seconds": round(total_time, 2),
                "total_tokens": total_tokens,
                "projects": summary
            }, f, indent=2)
        print(f"  Summary saved to: {summary_path}\n")
    except Exception as e:
        print(f"  Failed to save summary JSON: {e}\n")

if __name__ == "__main__":
    main()
