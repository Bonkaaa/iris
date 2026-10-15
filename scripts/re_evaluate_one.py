import os
import sys
import json
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import DATA_DIR, OUTPUT_DIR, ALL_METHOD_INFO_DIR, PROJECT_SOURCE_CODE_DIR
from src.modules.evaluation_pipeline import EvaluationPipeline

slug = "joniles__mpxj_CVE-2020-35460_8.3.4"
run_id = "test_run"
query = "cwe-022wLLM"

project_output_path = Path(OUTPUT_DIR) / slug / run_id
analysis_common_path = project_output_path / "analysis" / "common"
analysis_cwe_path = project_output_path / "analysis" / query
query_output_path = project_output_path / query
posthoc_path = project_output_path / f"{query}-posthoc-filter"

fixed_methods = pd.read_csv(ALL_METHOD_INFO_DIR)
project_fixed_methods = fixed_methods[fixed_methods["project_slug"] == slug]

class_locs_path = project_output_path / "fetch_class_locs" / "results.csv"
func_locs_path = project_output_path / "fetch_func_locs" / "results.csv"

sarif_path = query_output_path / "results.sarif"
final_json_path = project_output_path / f"{query}-final" / "results.json"

eval_pipe = EvaluationPipeline(
    project_fixed_methods=project_fixed_methods,
    class_locs_path=str(class_locs_path),
    func_locs_path=str(func_locs_path),
    project_source_code_dir=str(Path(PROJECT_SOURCE_CODE_DIR) / slug),
    external_apis_csv_path=str(project_output_path / "fetch_external_apis" / "results.csv"),
    candidate_apis_csv_path=str(analysis_common_path / "candidate_apis.csv"),
    llm_labelled_sink_apis_path=str(analysis_cwe_path / "llm_labelled_sink_apis.json"),
    llm_labelled_source_apis_path=str(analysis_cwe_path / "llm_labelled_source_apis.json"),
    llm_labelled_taint_prop_apis_path=str(analysis_cwe_path / "llm_labelled_taint_prop_apis.json"),
    source_func_param_candidates_path=str(analysis_common_path / "source_func_param_candidates.csv"),
    llm_labelled_source_func_params_path=str(analysis_cwe_path / "llm_labelled_source_func_params.json"),
    query_output_result_sarif_path=str(sarif_path),
    posthoc_filtering_output_result_sarif_path=str(posthoc_path / "results.sarif"),
    final_output_json_path=str(final_json_path),
    overwrite=True
)

res = eval_pipe.evaluate_sarif_result(str(sarif_path))
print("--- SARIF EVALUATION RESULT ---")
print(json.dumps(res, indent=2))

# Also update the final results.json
if final_json_path.exists():
    with open(final_json_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    existing["vanilla_result"] = res
    existing["posthoc_filter_result"] = res
    with open(final_json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    print(f"\nUpdated {final_json_path} successfully!")
