import shutil
import os

IRIS_ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")

# CODEQL_DIR resolution
local_codeql = f"{IRIS_ROOT_DIR}/codeql"
if os.path.exists(local_codeql):
    CODEQL_DIR = local_codeql
elif "CODEQL_DIR" in os.environ:
    CODEQL_DIR = os.environ["CODEQL_DIR"]
elif shutil.which("codeql"):
    CODEQL_DIR = os.path.dirname(shutil.which("codeql"))
else:
    CODEQL_DIR = local_codeql

# Determine executable path (prefer bundled codeql in CODEQL_DIR)
if os.name == 'nt':
    if os.path.exists(f"{CODEQL_DIR}/codeql.exe"):
        CODEQL_BIN = os.path.abspath(f"{CODEQL_DIR}/codeql.exe")
    elif os.path.exists(f"{CODEQL_DIR}/codeql.cmd"):
        CODEQL_BIN = os.path.abspath(f"{CODEQL_DIR}/codeql.cmd")
    elif shutil.which("codeql"):
        CODEQL_BIN = shutil.which("codeql")
    else:
        CODEQL_BIN = f"{CODEQL_DIR}/codeql.cmd"
else:
    # Linux / Docker container
    if os.path.exists(f"{CODEQL_DIR}/codeql") and not os.path.isdir(f"{CODEQL_DIR}/codeql"):
        CODEQL_BIN = os.path.abspath(f"{CODEQL_DIR}/codeql")
    elif shutil.which("codeql"):
        CODEQL_BIN = shutil.which("codeql")
    else:
        CODEQL_BIN = f"{CODEQL_DIR}/codeql"

# DATA_DIR points to active dataset directory (set to z_data for custom VIC benchmark)
DATA_DIR = f"{IRIS_ROOT_DIR}/z_data"

# CODEQL_DB_PATH is the path to the directory that contains CodeQL databases.
CODEQL_DB_PATH = f"{DATA_DIR}/codeql-dbs"

# PROJECT_SOURCE_CODE_DIR contains the Java projects. 
PROJECT_SOURCE_CODE_DIR = f"{DATA_DIR}/project-sources"

# PACKAGE_MODULES_PATH contains each project's internal modules. 
PACKAGE_MODULES_PATH = f"{DATA_DIR}/package-names"

# OUTPUT_DIR is where the results from running Iris are stored.
OUTPUT_DIR = f"{IRIS_ROOT_DIR}/output"

# ALL_METHOD_INFO_DIR  
ALL_METHOD_INFO_DIR = f"{DATA_DIR}/fix_info.csv"

# BUILD INFO DIR 
BUILD_INFO = f"{DATA_DIR}/build_info.csv"

# CVES_MAPPED_W_COMMITS_DIR is the path to project_info.csv, which contains the mapping of vulnerabilities to projects in cwe-bench-java. 
CVES_MAPPED_W_COMMITS_DIR = f"{DATA_DIR}/project_info.csv"

DEP_CONFIGS = f"{IRIS_ROOT_DIR}/dep_configs.json"

# this must be changed when the CodeQL query version is updated
# CODEQL_QUERY_VERSION is the version of the CodeQL queries used in Iris.
# This values should match qlpacks/codeql/java-queries/{CODEQL_QUERY_VERSION}
CODEQL_QUERY_VERSION = "1.8.1"
