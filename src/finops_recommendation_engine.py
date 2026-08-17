import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# FINOPS RECOMMENDATION ENGINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "cloud_cost_data.csv"
ANOMALY_FILE = BASE_DIR / "results" / "cost_anomalies.csv"
OUTPUT_FILE = BASE_DIR / "results" / "finops_recommendations.csv"


def generate_recommendation(row):
    """
    Generate an explainable FinOps recommendation
    using cost, anomaly severity, usage hours,
    storage and data transfer.
    """

    service = str(row["Service"]).lower()
    cost = float(row["Monthly_Cost"])
    usage_hours = float(row["Usage_Hours"])
    storage = float(row["Storage_GB"])
    transfer = float(row["Data_Transfer_GB"])
    severity = str(row["Anomaly_Severity"])

    # --------------------------------------------------------
    # HIGH anomaly
    # --------------------------------------------------------

    if severity == "HIGH":

        if service in [
            "ec2",
            "rds",
            "compute engine",
            "virtual machines"
        ]:

            recommendation = (
                "Investigate unusually high compute spending; "
                "review resource sizing, utilization and "
                "instance configuration."
            )

            priority = "CRITICAL"

        elif storage > 1000:

            recommendation = (
                "Review high storage consumption and consider "
                "lifecycle policies, archival or storage cleanup."
            )

            priority = "HIGH"

        elif transfer > 350:

            recommendation = (
                "Investigate unusually high data transfer and "
                "review network architecture and transfer patterns."
            )

            priority = "HIGH"

        else:

            recommendation = (
                "Investigate this unusually high cloud cost "
                "and compare it with expected usage."
            )

            priority = "HIGH"

    # --------------------------------------------------------
    # MEDIUM anomaly
    # --------------------------------------------------------

    elif severity == "MEDIUM":

        if usage_hours > 600:

            recommendation = (
                "Review compute usage hours and consider "
                "scheduling, rightsizing or workload optimization."
            )

            priority = "MEDIUM"

        elif storage > 1000:

            recommendation = (
                "Review storage utilization and consider "
                "lifecycle management or archival."
            )

            priority = "MEDIUM"

        elif transfer > 350:

            recommendation = (
                "Review data transfer usage and identify "
                "potential network optimization opportunities."
            )

            priority = "MEDIUM"

        else:

            recommendation = (
                "Monitor this cost closely and investigate "
                "the underlying usage pattern."
            )

            priority = "MEDIUM"

    # --------------------------------------------------------
    # Normal records
    # --------------------------------------------------------

    else:

        if cost > 300:

            recommendation = (
                "Monitor relatively high recurring cost "
                "and evaluate optimization opportunities."
            )

            priority = "LOW"

        else:

            recommendation = (
                "No immediate optimization action required."
            )

            priority = "NORMAL"

    # --------------------------------------------------------
    # Estimated savings
    # --------------------------------------------------------

    savings_rate = {
        "CRITICAL": 0.20,
        "HIGH": 0.15,
        "MEDIUM": 0.10,
        "LOW": 0.05,
        "NORMAL": 0.00
    }

    saving_percent = savings_rate.get(priority, 0.00)

    potential_saving = cost * saving_percent

    return pd.Series({
        "Recommendation": recommendation,
        "Priority": priority,
        "Potential_Saving_Percent": saving_percent * 100,
        "Potential_Saving": round(potential_saving, 2)
    })


def main():

    print("=" * 65)
    print("FINOPS CLOUD COST RECOMMENDATION ENGINE")
    print("=" * 65)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    print("\nLoading cloud cost dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Dataset records: {len(df):,}")

    # --------------------------------------------------------
    # Load anomaly results
    # --------------------------------------------------------

    print("\nLoading anomaly results...")

    anomalies = pd.read_csv(ANOMALY_FILE)

    print(f"Anomaly records: {len(anomalies):,}")

    # --------------------------------------------------------
    # Merge anomaly information
    # --------------------------------------------------------

    merge_columns = [
        "Account_ID",
        "Cloud_Provider",
        "Service",
        "Region",
        "Usage_Date",
        "Monthly_Cost"
    ]

    anomaly_columns = merge_columns + [
        "Anomaly_Severity"
    ]

    anomalies_subset = anomalies[anomaly_columns].copy()

    df = df.merge(
        anomalies_subset,
        on=merge_columns,
        how="left"
    )

    # --------------------------------------------------------
    # Fill non-anomalous records
    # --------------------------------------------------------

    df["Anomaly_Severity"] = (
        df["Anomaly_Severity"]
        .fillna("NORMAL")
    )

    # --------------------------------------------------------
    # Generate recommendations
    # --------------------------------------------------------

    print("\nGenerating FinOps recommendations...")

    recommendations = df.apply(
        generate_recommendation,
        axis=1
    )

    df = pd.concat(
        [df, recommendations],
        axis=1
    )

    # --------------------------------------------------------
    # Sort by priority and potential saving
    # --------------------------------------------------------

    priority_order = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
        "NORMAL": 5
    }

    df["Priority_Rank"] = (
        df["Priority"]
        .map(priority_order)
    )

    df = df.sort_values(
        by=[
            "Priority_Rank",
            "Potential_Saving"
        ],
        ascending=[
            True,
            False
        ]
    )

    # --------------------------------------------------------
    # Select final columns
    # --------------------------------------------------------

    output_columns = [
        "Account_ID",
        "Cloud_Provider",
        "Service",
        "Region",
        "Usage_Date",
        "Usage_Hours",
        "Data_Transfer_GB",
        "Storage_GB",
        "Monthly_Cost",
        "Anomaly_Severity",
        "Recommendation",
        "Priority",
        "Potential_Saving_Percent",
        "Potential_Saving"
    ]

    final_df = df[output_columns]

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    final_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("FINOPS RECOMMENDATION SUMMARY")
    print("=" * 65)

    print(
        f"\nTotal records analyzed: "
        f"{len(final_df):,}"
    )

    print("\nRecommendations by priority:")

    priority_summary = (
        final_df["Priority"]
        .value_counts()
    )

    for priority, count in priority_summary.items():

        print(
            f"{priority:<10} {count:,}"
        )

    # --------------------------------------------------------
    # Potential savings
    # --------------------------------------------------------

    total_potential_saving = (
        final_df["Potential_Saving"]
        .sum()
    )

    print(
        f"\nEstimated optimization opportunity: "
        f"${total_potential_saving:,.2f}"
    )

    # --------------------------------------------------------
    # Top recommendations
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("TOP 15 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 65)

    display_columns = [
        "Account_ID",
        "Cloud_Provider",
        "Service",
        "Monthly_Cost",
        "Anomaly_Severity",
        "Priority",
        "Potential_Saving"
    ]

    print(
        final_df[
            display_columns
        ]
        .head(15)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Provider summary
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("OPTIMIZATION OPPORTUNITY BY PROVIDER")
    print("=" * 65)

    provider_summary = (
        final_df
        .groupby("Cloud_Provider")
        .agg(
            Total_Cost=("Monthly_Cost", "sum"),
            Potential_Saving=("Potential_Saving", "sum")
        )
        .sort_values(
            "Potential_Saving",
            ascending=False
        )
    )

    print(
        provider_summary.to_string()
    )

    # --------------------------------------------------------
    # Service summary
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("OPTIMIZATION OPPORTUNITY BY SERVICE")
    print("=" * 65)

    service_summary = (
        final_df
        .groupby("Service")
        .agg(
            Total_Cost=("Monthly_Cost", "sum"),
            Potential_Saving=("Potential_Saving", "sum")
        )
        .sort_values(
            "Potential_Saving",
            ascending=False
        )
    )

    print(
        service_summary.head(12).to_string()
    )

    print("\n" + "=" * 65)
    print("FINOPS RECOMMENDATION ENGINE COMPLETE")
    print("=" * 65)

    print(
        f"\nResults saved to:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()