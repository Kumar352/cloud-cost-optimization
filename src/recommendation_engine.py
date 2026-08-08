import pandas as pd
import os

# ============================================================
# CLOUD COST OPTIMIZATION - RECOMMENDATION ENGINE
# ============================================================

INPUT_FILE = "data/raw/cloud_cost_data.csv"
OUTPUT_FILE = "results/optimization_candidates.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load the cloud cost dataset."""

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    return df


# ============================================================
# CALCULATE COST THRESHOLD
# ============================================================

def calculate_cost_threshold(df):
    """
    Identify high-cost resources using the 90th percentile
    of Monthly_Cost.
    """

    return df["Monthly_Cost"].quantile(0.90)


# ============================================================
# SERVICE CATEGORY
# ============================================================

def get_service_category(service):

    service = str(service).lower()

    if any(word in service for word in [
        "ec2",
        "virtual machines",
        "compute engine"
    ]):
        return "Compute"

    if any(word in service for word in [
        "s3",
        "blob storage",
        "cloud storage"
    ]):
        return "Storage"

    if any(word in service for word in [
        "rds",
        "azure sql",
        "cloud sql"
    ]):
        return "Database"

    if any(word in service for word in [
        "lambda",
        "functions",
        "cloud functions"
    ]):
        return "Serverless"

    return "Other"


# ============================================================
# GENERATE RECOMMENDATION
# ============================================================

def generate_recommendation(row, cost_threshold):

    service = str(row["Service"])
    category = get_service_category(service)

    monthly_cost = float(row["Monthly_Cost"])

    # --------------------------------------------------------
    # Only high-cost resources need optimization
    # --------------------------------------------------------

    if monthly_cost < cost_threshold:

        return (
            "No Immediate Action",
            "LOW"
        )

    # --------------------------------------------------------
    # Compute recommendations
    # --------------------------------------------------------

    if category == "Compute":

        return (
            "Review Compute Usage",
            "HIGH"
        )

    # --------------------------------------------------------
    # Storage recommendations
    # --------------------------------------------------------

    if category == "Storage":

        return (
            "Review Storage Usage",
            "HIGH"
        )

    # --------------------------------------------------------
    # Database recommendations
    # --------------------------------------------------------

    if category == "Database":

        return (
            "Review Database Usage",
            "HIGH"
        )

    # --------------------------------------------------------
    # Serverless recommendations
    # --------------------------------------------------------

    if category == "Serverless":

        return (
            "Review Service Usage",
            "HIGH"
        )

    # --------------------------------------------------------
    # Generic recommendation
    # --------------------------------------------------------

    return (
        "Review Cloud Resource Usage",
        "MEDIUM"
    )


# ============================================================
# ADD DETAILED RECOMMENDATION
# ============================================================

def generate_action(row):

    service = str(row["Service"])
    category = get_service_category(service)

    if category == "Compute":

        return (
            "Check utilization and consider right-sizing "
            "the compute resource."
        )

    if category == "Storage":

        return (
            "Review stored data, remove unnecessary storage, "
            "and consider lifecycle policies."
        )

    if category == "Database":

        return (
            "Review database utilization, sizing, and "
            "scaling requirements."
        )

    if category == "Serverless":

        return (
            "Review invocation patterns, execution usage, "
            "and unnecessary workloads."
        )

    return (
        "Review resource utilization and monthly spending."
    )


# ============================================================
# RUN RECOMMENDATION ENGINE
# ============================================================

def run_recommendation_engine():

    print("=" * 60)
    print("CLOUD COST OPTIMIZATION RECOMMENDATION ENGINE")
    print("=" * 60)

    # Load dataset
    df = load_data()

    print(f"Records loaded: {len(df)}")

    # Calculate threshold
    cost_threshold = calculate_cost_threshold(df)

    print(
        f"High-cost threshold (90th percentile): "
        f"${cost_threshold:.2f}"
    )

    # --------------------------------------------------------
    # Generate recommendations
    # --------------------------------------------------------

    recommendations = df.apply(
        lambda row: generate_recommendation(
            row,
            cost_threshold
        ),
        axis=1
    )

    df["Recommendation"] = recommendations.apply(
        lambda x: x[0]
    )

    df["Optimization_Priority"] = recommendations.apply(
        lambda x: x[1]
    )

    # --------------------------------------------------------
    # Detailed action
    # --------------------------------------------------------

    df["Recommended_Action"] = df.apply(
        generate_action,
        axis=1
    )

    # --------------------------------------------------------
    # Optimization flag
    # --------------------------------------------------------

    df["Optimization_Flag"] = df["Monthly_Cost"].apply(
        lambda cost:
        "High Cost"
        if cost >= cost_threshold
        else "Normal Cost"
    )

    # --------------------------------------------------------
    # Optimization score
    # --------------------------------------------------------

    df["Optimization_Score"] = (
        df["Monthly_Cost"] / df["Monthly_Cost"].max()
    ) * 100

    df["Optimization_Score"] = (
        df["Optimization_Score"]
        .round(2)
    )

    # --------------------------------------------------------
    # Sort highest priority resources first
    # --------------------------------------------------------

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    df["_Priority_Order"] = (
        df["Optimization_Priority"]
        .map(priority_order)
    )

    df = df.sort_values(
        by=[
            "_Priority_Order",
            "Monthly_Cost"
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
    # Create output directory
    # --------------------------------------------------------

    os.makedirs(
        "results",
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save complete recommendation dataset
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    high_cost_df = df[
        df["Optimization_Flag"] == "High Cost"
    ]

    high_cost_spending = (
        high_cost_df["Monthly_Cost"].sum()
    )

    potential_savings = (
        high_cost_spending * 0.15
    )

    print()
    print("=" * 60)
    print("RECOMMENDATION ENGINE RESULTS")
    print("=" * 60)

    print(
        f"Total Records: {len(df)}"
    )

    print(
        f"High-Cost Records: {len(high_cost_df)}"
    )

    print(
        f"High-Cost Spending: "
        f"${high_cost_spending:,.2f}"
    )

    print(
        f"Potential Monthly Savings (15%): "
        f"${potential_savings:,.2f}"
    )

    print()
    print("Optimization Priority:")

    print(
        df["Optimization_Priority"]
        .value_counts()
    )

    print()
    print("Recommendation Categories:")

    print(
        df["Recommendation"]
        .value_counts()
    )

    print()
    print(
        f"Results saved to: {OUTPUT_FILE}"
    )

    print("=" * 60)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_recommendation_engine()