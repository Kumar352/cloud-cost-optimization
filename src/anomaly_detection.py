import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CLOUD COST ANOMALY DETECTION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "cloud_cost_data.csv"
OUTPUT_FILE = BASE_DIR / "results" / "cost_anomalies.csv"


def detect_anomalies(df):
    """
    Detect unusually high monthly costs using the IQR method.

    IQR = Q3 - Q1

    Upper Bound = Q3 + 1.5 * IQR

    Any cost above the upper bound is considered an anomaly.
    """

    q1 = df["Monthly_Cost"].quantile(0.25)
    q3 = df["Monthly_Cost"].quantile(0.75)

    iqr = q3 - q1

    upper_bound = q3 + (1.5 * iqr)

    df["Anomaly_Threshold"] = upper_bound

    df["Is_Anomaly"] = df["Monthly_Cost"] > upper_bound

    df["Anomaly_Severity"] = np.where(
        df["Monthly_Cost"] > upper_bound * 1.5,
        "HIGH",
        np.where(
            df["Monthly_Cost"] > upper_bound,
            "MEDIUM",
            "NORMAL"
        )
    )

    return df, q1, q3, iqr, upper_bound


def main():

    print("=" * 60)
    print("CLOUD COST ANOMALY DETECTION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------

    print("\nLoading cloud cost dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Records loaded: {len(df):,}")

    # --------------------------------------------------------
    # Convert date
    # --------------------------------------------------------

    df["Usage_Date"] = pd.to_datetime(df["Usage_Date"])

    # --------------------------------------------------------
    # Detect anomalies
    # --------------------------------------------------------

    df, q1, q3, iqr, upper_bound = detect_anomalies(df)

    anomalies = df[df["Is_Anomaly"]].copy()

    # --------------------------------------------------------
    # Sort anomalies by cost
    # --------------------------------------------------------

    anomalies = anomalies.sort_values(
        by="Monthly_Cost",
        ascending=False
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    anomalies.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Display analysis
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ANOMALY STATISTICS")
    print("=" * 60)

    print(f"\nQ1 Cost:             ${q1:,.2f}")
    print(f"Q3 Cost:             ${q3:,.2f}")
    print(f"IQR:                 ${iqr:,.2f}")
    print(f"Anomaly Threshold:   ${upper_bound:,.2f}")

    print(f"\nTotal records:       {len(df):,}")
    print(f"Anomalies detected:  {len(anomalies):,}")

    anomaly_percentage = (
        len(anomalies) / len(df) * 100
    )

    print(
        f"Anomaly percentage:  {anomaly_percentage:.2f}%"
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ANOMALY SEVERITY")
    print("=" * 60)

    severity_counts = (
        anomalies["Anomaly_Severity"]
        .value_counts()
    )

    for severity, count in severity_counts.items():
        print(f"{severity:<10} {count}")

    # --------------------------------------------------------
    # Top anomalies
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("TOP 10 COST ANOMALIES")
    print("=" * 60)

    if len(anomalies) > 0:

        display_columns = [
            "Account_ID",
            "Cloud_Provider",
            "Service",
            "Region",
            "Usage_Date",
            "Monthly_Cost",
            "Anomaly_Severity"
        ]

        print(
            anomalies[
                display_columns
            ]
            .head(10)
            .to_string(index=False)
        )

    else:

        print("\nNo anomalies detected.")

    # --------------------------------------------------------
    # Provider anomaly summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ANOMALIES BY CLOUD PROVIDER")
    print("=" * 60)

    if len(anomalies) > 0:

        provider_summary = (
            anomalies
            .groupby("Cloud_Provider")
            .agg(
                Anomaly_Count=("Monthly_Cost", "count"),
                Anomaly_Cost=("Monthly_Cost", "sum")
            )
            .sort_values(
                "Anomaly_Cost",
                ascending=False
            )
        )

        print(
            provider_summary.to_string()
        )

    # --------------------------------------------------------
    # Service anomaly summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("ANOMALIES BY SERVICE")
    print("=" * 60)

    if len(anomalies) > 0:

        service_summary = (
            anomalies
            .groupby("Service")
            .agg(
                Anomaly_Count=("Monthly_Cost", "count"),
                Anomaly_Cost=("Monthly_Cost", "sum")
            )
            .sort_values(
                "Anomaly_Cost",
                ascending=False
            )
        )

        print(
            service_summary.head(10).to_string()
        )

    print("\n" + "=" * 60)
    print("ANOMALY DETECTION COMPLETE")
    print("=" * 60)

    print(
        f"\nResults saved to:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()