import pandas as pd
import os

# ============================================================
# CLOUD COST OPTIMIZATION
# UNDERUTILIZATION DETECTION ENGINE
# ============================================================

INPUT_FILE = "data/raw/cloud_cost_data.csv"
OUTPUT_FILE = "results/underutilized_resources.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    return pd.read_csv(INPUT_FILE)


# ============================================================
# CALCULATE BASELINE VALUES
# ============================================================

def calculate_baselines(df):

    median_usage = df["Usage_Hours"].median()
    median_cost = df["Monthly_Cost"].median()
    median_cost_per_hour = df["Cost_Per_Hour"].median()

    return (
        median_usage,
        median_cost,
        median_cost_per_hour
    )


# ============================================================
# CALCULATE COST PER HOUR
# ============================================================

def calculate_cost_per_hour(df):

    df["Cost_Per_Hour"] = (
        df["Monthly_Cost"]
        / df["Usage_Hours"].replace(0, 1)
    )

    return df


# ============================================================
# UNDERUTILIZATION SCORE
# ============================================================

def calculate_score(row, median_usage, median_cost):

    usage_ratio = (
        row["Usage_Hours"]
        / max(median_usage, 1)
    )

    cost_ratio = (
        row["Monthly_Cost"]
        / max(median_cost, 1)
    )

    # Lower usage increases the score
    usage_component = max(
        0,
        1 - usage_ratio
    ) * 60

    # Higher cost increases the score
    cost_component = min(
        cost_ratio / 2,
        1
    ) * 40

    score = usage_component + cost_component

    return round(score, 2)


# ============================================================
# CLASSIFY RESOURCE
# ============================================================

def classify_resource(
    row,
    median_usage,
    median_cost,
    median_cost_per_hour
):

    low_usage = (
        row["Usage_Hours"] < median_usage
    )

    high_cost = (
        row["Monthly_Cost"] > median_cost
    )

    expensive_usage = (
        row["Cost_Per_Hour"]
        > median_cost_per_hour
    )

    # --------------------------------------------------------
    # HIGH UNDERUTILIZATION
    # --------------------------------------------------------

    if (
        low_usage
        and high_cost
        and expensive_usage
    ):

        return "HIGH"

    # --------------------------------------------------------
    # MEDIUM UNDERUTILIZATION
    # --------------------------------------------------------

    if (
        (low_usage and expensive_usage)
        or
        (low_usage and high_cost)
    ):

        return "MEDIUM"

    # --------------------------------------------------------
    # NORMAL
    # --------------------------------------------------------

    return "LOW"


# ============================================================
# GENERATE ACTION
# ============================================================

def generate_action(row, priority):

    service = str(row["Service"]).lower()

    if priority == "LOW":

        return (
            "No immediate action. Continue monitoring "
            "resource utilization and cost."
        )

    if (
        "ec2" in service
        or "virtual machine" in service
        or "compute engine" in service
    ):

        return (
            "Review compute utilization, consider "
            "right-sizing, scheduling, or removing "
            "unnecessary resources."
        )

    if (
        "s3" in service
        or "storage" in service
        or "blob" in service
    ):

        return (
            "Review stored data, remove unnecessary "
            "objects, and consider storage lifecycle policies."
        )

    if (
        "rds" in service
        or "sql" in service
    ):

        return (
            "Review database utilization and sizing. "
            "Consider scaling based on workload."
        )

    if (
        "lambda" in service
        or "function" in service
    ):

        return (
            "Review invocation and execution patterns "
            "and identify unnecessary workloads."
        )

    return (
        "Review resource utilization and determine "
        "whether the resource can be reduced or removed."
    )


# ============================================================
# RUN DETECTION ENGINE
# ============================================================

def run_underutilization_detector():

    print("=" * 65)
    print("CLOUD COST UNDERUTILIZATION DETECTION ENGINE")
    print("=" * 65)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_data()

    print(
        f"Records loaded: {len(df)}"
    )

    # --------------------------------------------------------
    # Calculate cost per hour
    # --------------------------------------------------------

    df = calculate_cost_per_hour(df)

    # --------------------------------------------------------
    # Calculate baselines
    # --------------------------------------------------------

    (
        median_usage,
        median_cost,
        median_cost_per_hour
    ) = calculate_baselines(df)

    print(
        f"Median Usage: "
        f"{median_usage:.2f} hours"
    )

    print(
        f"Median Monthly Cost: "
        f"${median_cost:.2f}"
    )

    print(
        f"Median Cost Per Hour: "
        f"${median_cost_per_hour:.4f}"
    )

    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    df["Underutilization_Score"] = df.apply(
        lambda row:
        calculate_score(
            row,
            median_usage,
            median_cost
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Priority classification
    # --------------------------------------------------------

    df["Underutilization_Priority"] = df.apply(
        lambda row:
        classify_resource(
            row,
            median_usage,
            median_cost,
            median_cost_per_hour
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Underutilization flag
    # --------------------------------------------------------

    df["Underutilization_Flag"] = (
        df["Underutilization_Priority"]
        .apply(
            lambda value:
            "YES"
            if value in ["HIGH", "MEDIUM"]
            else "NO"
        )
    )

    # --------------------------------------------------------
    # Generate action
    # --------------------------------------------------------

    df["Underutilization_Action"] = df.apply(
        lambda row:
        generate_action(
            row,
            row["Underutilization_Priority"]
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Sort results
    # --------------------------------------------------------

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    df["_Priority_Order"] = (
        df["Underutilization_Priority"]
        .map(priority_order)
    )

    df = df.sort_values(
        by=[
            "_Priority_Order",
            "Underutilization_Score"
        ],
        ascending=[
            True,
            False
        ]
    )

    df = df.drop(
        columns=["_Priority_Order"]
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    os.makedirs(
        "results",
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    high_df = df[
        df["Underutilization_Priority"] == "HIGH"
    ]

    medium_df = df[
        df["Underutilization_Priority"] == "MEDIUM"
    ]

    flagged_df = df[
        df["Underutilization_Flag"] == "YES"
    ]

    flagged_spending = (
        flagged_df["Monthly_Cost"].sum()
    )

    potential_savings = (
        flagged_spending * 0.20
    )

    print()
    print("=" * 65)
    print("UNDERUTILIZATION RESULTS")
    print("=" * 65)

    print(
        f"Total Records: {len(df)}"
    )

    print(
        f"High Priority Resources: "
        f"{len(high_df)}"
    )

    print(
        f"Medium Priority Resources: "
        f"{len(medium_df)}"
    )

    print(
        f"Total Underutilization Candidates: "
        f"{len(flagged_df)}"
    )

    print(
        f"Candidate Spending: "
        f"${flagged_spending:,.2f}"
    )

    print(
        f"Potential Savings Scenario (20%): "
        f"${potential_savings:,.2f}"
    )

    print()
    print("Underutilization Priority:")

    print(
        df["Underutilization_Priority"]
        .value_counts()
    )

    print()
    print(
        f"Results saved to: {OUTPUT_FILE}"
    )

    print("=" * 65)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_underutilization_detector()