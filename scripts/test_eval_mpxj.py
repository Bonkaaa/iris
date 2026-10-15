import json
from pathlib import Path

sarif_path = Path("output/joniles__mpxj_CVE-2020-35460_8.3.4/test_run/cwe-022wLLM/results.sarif")
data = json.load(open(sarif_path))

runs = data["runs"]
results = runs[0]["results"]
print(f"Total results: {len(results)}")

for idx, res in enumerate(results):
    print(f"\n--- Result #{idx} ---")
    message = res.get("message", {}).get("text", "")
    print(f"Message: {message[:100]}")
    code_flows = res.get("codeFlows", [])
    print(f"CodeFlows count: {len(code_flows)}")
    for j, cf in enumerate(code_flows):
        tflow = cf["threadFlows"][0]
        locations = tflow["locations"]
        print(f"  Flow #{j}: {len(locations)} steps")
        for k, loc in enumerate(locations):
            ploc = loc["location"]["physicalLocation"]
            uri = ploc["artifactLocation"]["uri"]
            line = ploc["region"]["startLine"]
            msg = loc["location"].get("message", {}).get("text", "")
            print(f"    [{k}] {uri}:{line} -> {msg[:60]}")
