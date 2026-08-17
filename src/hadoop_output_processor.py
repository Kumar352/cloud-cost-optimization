import subprocess
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

HADOOP_BIN = (
    r"C:\Users\kumardereddy\OneDrive\Desktop\BigData"
    r"\hadoop-3.2.2\bin\hdfs.cmd"
)

HDFS_OUTPUT = (
    "/cloud_cost_project/processed/"
    "cloud_cost_analysis/part-r-00000"
)

RESULTS_DIR = Path("results")

PROVIDER_OUTPUT = RESULTS_DIR / "hadoop_provider_costs.csv"
SERVICE_OUTPUT = RESULTS_DIR / "hadoop_service_costs.csv"
REGION_OUTPUT = RESULTS_DIR / "hadoop_region_costs.csv"


# ============================================================
# READ HADOOP OUTPUT
# ============================================================

def read_hadoop_output():

    command = [
        HADOOP_BIN,
        "dfs",
        "-cat",
        HDFS_OUTPUT
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        shell=False
    )

    return result.stdout.strip().splitlines()


# ============================================================
# PARSE HADOOP OUTPUT
# ============================================================

def parse_output(lines):

    provider_rows = []
    service_rows = []
    region_rows = []

    for line in lines:

        if not line.strip():
            continue

        # Hadoop output format:
        #
        # PROVIDER|AWS       859892.39
        # SERVICE|EC2        328055.28
        # REGION|eastus     225447.96

        parts = line.split("|", 1)

        if len(parts) != 2:
            continue

        category = parts[0].strip()

        remaining = parts[1].strip()

        # Separate name and numeric cost
        value_parts = remaining.rsplit(None, 1)

        if len(value_parts) != 2:
            continue

        name = value_parts[0].strip()
        cost = float(value_parts[1])

        if category == "PROVIDER":

            provider_rows.append({
                "Cloud_Provider": name,
                "Monthly_Cost": cost
            })

        elif category == "SERVICE":

            service_rows.append({
                "Service": name,
                "Monthly_Cost": cost
            })

        elif category == "REGION":

            region_rows.append({
                "Region": name,
                "Monthly_Cost": cost
            })

    return (
        provider_rows,
        service_rows,
        region_rows
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    provider_rows,
    service_rows,
    region_rows
):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    provider_df = pd.DataFrame(
        provider_rows
    )

    service_df = pd.DataFrame(
        service_rows
    )

    region_df = pd.DataFrame(
        region_rows
    )

    provider_df.to_csv(
        PROVIDER_OUTPUT,
        index=False
    )

    service_df.to_csv(
        SERVICE_OUTPUT,
        index=False
    )

    region_df.to_csv(
        REGION_OUTPUT,
        index=False
    )

    return (
        provider_df,
        service_df,
        region_df
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("HADOOP → PYTHON CLOUD COST INTEGRATION")
    print("=" * 60)

    print("\nReading Hadoop output from HDFS...")

    lines = read_hadoop_output()

    print(
        f"Lines received from Hadoop: {len(lines)}"
    )

    (
        provider_rows,
        service_rows,
        region_rows
    ) = parse_output(lines)

    (
        provider_df,
        service_df,
        region_df
    ) = save_results(
        provider_rows,
        service_rows,
        region_rows
    )

    print("\nHadoop results successfully processed.")

    print(
        f"\nProvider records: {len(provider_df)}"
    )

    print(
        f"Service records: {len(service_df)}"
    )

    print(
        f"Region records: {len(region_df)}"
    )

    # --------------------------------------------------------
    # PROVIDER SUMMARY
    # --------------------------------------------------------

    print("\nProvider Cost Summary:")
    print(
        provider_df.to_string(index=False)
    )

    # --------------------------------------------------------
    # SERVICE SUMMARY
    # --------------------------------------------------------

    print("\nService Cost Summary:")
    print(
        service_df.to_string(index=False)
    )

    # --------------------------------------------------------
    # REGION SUMMARY
    # --------------------------------------------------------

    print("\nRegion Cost Summary:")
    print(
        region_df.to_string(index=False)
    )

    # --------------------------------------------------------
    # TOTAL COST VALIDATION
    # --------------------------------------------------------

    total_cost = provider_df[
        "Monthly_Cost"
    ].sum()

    print(
        f"\nTotal Hadoop Cost: "
        f"${total_cost:,.2f}"
    )

    print("\nExpected Python Dataset Total:")
    print("$2,402,237.28")

    difference = (
        total_cost - 2402237.28
    )

    print(
        f"Validation Difference: "
        f"${difference:,.2f}"
    )

    if abs(difference) < 0.01:

        print(
            "\nVALIDATION: PASSED"
        )

        print(
            "Hadoop total matches "
            "the Python dataset total."
        )

    else:

        print(
            "\nVALIDATION: CHECK REQUIRED"
        )

    # --------------------------------------------------------
    # OUTPUT FILES
    # --------------------------------------------------------

    print("\nFiles saved:")

    print(
        f"  {PROVIDER_OUTPUT}"
    )

    print(
        f"  {SERVICE_OUTPUT}"
    )

    print(
        f"  {REGION_OUTPUT}"
    )

    print("\n" + "=" * 60)
    print("HADOOP → PYTHON INTEGRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()