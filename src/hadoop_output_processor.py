import os
import subprocess
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
HADOOP_HOME = Path(
    os.environ.get(
        "HADOOP_HOME",
        str(Path.home() / "OneDrive" / "Desktop" / "BigData" / "hadoop-3.2.2"),
    )
)
HADOOP_BIN = HADOOP_HOME / "bin" / ("hdfs.cmd" if os.name == "nt" else "hdfs")
HDFS_OUTPUT = os.environ.get(
    "CLOUD_COST_HDFS_OUTPUT",
    "/cloud_cost_project/processed/cloud_cost_analysis/part-r-00000",
)
INPUT_FILE = BASE_DIR / "data" / "raw" / "cloud_cost_data.csv"

RESULTS_DIR = BASE_DIR / "results"
PROVIDER_OUTPUT = RESULTS_DIR / "hadoop_provider_costs.csv"
SERVICE_OUTPUT = RESULTS_DIR / "hadoop_service_costs.csv"
REGION_OUTPUT = RESULTS_DIR / "hadoop_region_costs.csv"


# ============================================================
# READ HADOOP OUTPUT
# ============================================================

def read_hadoop_output():
    if not HADOOP_BIN.is_file():
        raise FileNotFoundError(
            f"Hadoop HDFS command not found: {HADOOP_BIN}. "
            "Set HADOOP_HOME to your Hadoop installation directory."
        )

    command = [str(HADOOP_BIN), "dfs", "-cat", HDFS_OUTPUT]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    )
    return result.stdout.strip().splitlines()


# ============================================================
# PARSE MAPREDUCE OUTPUT
# ============================================================

def parse_output(lines):
    provider_rows = []
    service_rows = []
    region_rows = []

    for line in lines:
        if not line.strip():
            continue

        # Expected formats, with a tab or spaces before the cost:
        # PROVIDER|AWS       859892.39
        # SERVICE|EC2        328055.28
        # REGION|us-east-1   225447.96
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue

        category = parts[0].strip()
        value_parts = parts[1].strip().rsplit(None, 1)
        if len(value_parts) != 2:
            continue

        name = value_parts[0].strip()
        try:
            cost = float(value_parts[1])
        except ValueError:
            continue

        if category == "PROVIDER":
            provider_rows.append({"Cloud_Provider": name, "Monthly_Cost": cost})
        elif category == "SERVICE":
            service_rows.append({"Service": name, "Monthly_Cost": cost})
        elif category == "REGION":
            region_rows.append({"Region": name, "Monthly_Cost": cost})

    return provider_rows, service_rows, region_rows


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(provider_rows, service_rows, region_rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    provider_df = pd.DataFrame(provider_rows, columns=["Cloud_Provider", "Monthly_Cost"])
    service_df = pd.DataFrame(service_rows, columns=["Service", "Monthly_Cost"])
    region_df = pd.DataFrame(region_rows, columns=["Region", "Monthly_Cost"])

    provider_df.to_csv(PROVIDER_OUTPUT, index=False)
    service_df.to_csv(SERVICE_OUTPUT, index=False)
    region_df.to_csv(REGION_OUTPUT, index=False)

    return provider_df, service_df, region_df


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("HADOOP -> PYTHON CLOUD COST INTEGRATION")
    print("=" * 60)
    print(f"\nReading Hadoop output from HDFS: {HDFS_OUTPUT}")

    lines = read_hadoop_output()
    print(f"Lines received from Hadoop: {len(lines)}")

    provider_rows, service_rows, region_rows = parse_output(lines)
    if not provider_rows:
        raise ValueError(
            "No PROVIDER summary rows were parsed from Hadoop output. "
            "Check the HDFS output path and reducer output format."
        )

    provider_df, service_df, region_df = save_results(
        provider_rows, service_rows, region_rows
    )

    print("\nHadoop results processed.")
    print(f"Provider records: {len(provider_df)}")
    print(f"Service records: {len(service_df)}")
    print(f"Region records: {len(region_df)}")

    print("\nProvider Cost Summary:")
    print(provider_df.to_string(index=False))
    print("\nService Cost Summary:")
    print(service_df.to_string(index=False))
    print("\nRegion Cost Summary:")
    print(region_df.to_string(index=False))

    total_cost = float(provider_df["Monthly_Cost"].sum())
    print("\nHadoop provider total: $" + format(total_cost, ",.2f"))

    if INPUT_FILE.is_file():
        raw_df = pd.read_csv(INPUT_FILE, usecols=["Monthly_Cost"])
        expected_total = float(pd.to_numeric(raw_df["Monthly_Cost"], errors="raise").sum())
        difference = total_cost - expected_total
        print("Current input dataset total: $" + format(expected_total, ",.2f"))
        print("Validation difference: $" + format(difference, ",.2f"))
        if abs(difference) < 0.01:
            print("VALIDATION: PASSED - Hadoop provider total matches the input CSV.")
        else:
            print(
                "VALIDATION: CHECK REQUIRED - Hadoop and CSV totals differ. "
                "Confirm both runs used the same dataset and billing units."
            )
    else:
        print(
            "Input CSV is unavailable, so a Python-dataset total comparison "
            "was skipped."
        )

    print("\nFiles saved:")
    print(f"  {PROVIDER_OUTPUT}")
    print(f"  {SERVICE_OUTPUT}")
    print(f"  {REGION_OUTPUT}")


if __name__ == "__main__":
    main()
