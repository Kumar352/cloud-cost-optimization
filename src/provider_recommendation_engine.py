import pandas as pd
import os

# ============================================================
# DATA-DRIVEN CLOUD PROVIDER RECOMMENDATION ENGINE
# ============================================================

INPUT_FILE = "data/raw/cloud_cost_data.csv"
OUTPUT_FILE = "results/provider_recommendations.csv"


# ============================================================
# SERVICE EQUIVALENCE MAPPING
# ============================================================

SERVICE_CATEGORY_MAP = {

    # --------------------------------------------------------
    # COMPUTE
    # --------------------------------------------------------

    "EC2": "Compute",
    "Virtual Machines": "Compute",
    "Compute Engine": "Compute",

    # --------------------------------------------------------
    # STORAGE
    # --------------------------------------------------------

    "S3": "Storage",
    "Blob Storage": "Storage",
    "Cloud Storage": "Storage",

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    "RDS": "Database",
    "Azure SQL": "Database",
    "Cloud SQL": "Database",

    # --------------------------------------------------------
    # SERVERLESS
    # --------------------------------------------------------

    "Lambda": "Serverless",
    "Functions": "Serverless",
    "Cloud Functions": "Serverless"
}


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
# MAP SERVICES TO COMMON CATEGORIES
# ============================================================

def map_service_categories(df):

    df = df.copy()

    df["Service_Category"] = (
        df["Service"]
        .map(SERVICE_CATEGORY_MAP)
    )

    return df


# ============================================================
# CALCULATE COST EFFICIENCY
# ============================================================

def calculate_cost_efficiency(df):

    df = df.copy()

    df["Cost_Per_Hour"] = (
        df["Monthly_Cost"]
        /
        df["Usage_Hours"].replace(
            0,
            1
        )
    )

    return df


# ============================================================
# CALCULATE PROVIDER BENCHMARKS
# ============================================================

def calculate_provider_benchmarks(df):

    benchmarks = (
        df.groupby(
            [
                "Service_Category",
                "Cloud_Provider"
            ]
        )
        .agg(
            Median_Cost_Per_Hour=(
                "Cost_Per_Hour",
                "median"
            ),

            Average_Cost_Per_Hour=(
                "Cost_Per_Hour",
                "mean"
            ),

            Resource_Count=(
                "Cost_Per_Hour",
                "count"
            )
        )
        .reset_index()
    )

    return benchmarks


# ============================================================
# GENERATE RECOMMENDATIONS
# ============================================================

def generate_recommendations(
    df,
    benchmarks
):

    results = []

    # --------------------------------------------------------
    # Process each resource
    # --------------------------------------------------------

    for _, row in df.iterrows():

        current_provider = (
            row["Cloud_Provider"]
        )

        service = row["Service"]

        service_category = (
            row["Service_Category"]
        )

        region = row["Region"]

        usage_hours = (
            row["Usage_Hours"]
        )

        current_cost = (
            row["Monthly_Cost"]
        )

        current_cost_per_hour = (
            row["Cost_Per_Hour"]
        )

        # ----------------------------------------------------
        # Check service category
        # ----------------------------------------------------

        if pd.isna(service_category):

            results.append({

                "Account_ID":
                    row["Account_ID"],

                "Current_Provider":
                    current_provider,

                "Current_Service":
                    service,

                "Service_Category":
                    "Unknown",

                "Region":
                    region,

                "Usage_Hours":
                    usage_hours,

                "Current_Monthly_Cost":
                    round(
                        current_cost,
                        2
                    ),

                "Current_Cost_Per_Hour":
                    round(
                        current_cost_per_hour,
                        4
                    ),

                "Recommended_Provider":
                    "No Recommendation",

                "Alternative_Cost_Per_Hour":
                    current_cost_per_hour,

                "Estimated_Alternative_Cost":
                    current_cost,

                "Estimated_Monthly_Savings":
                    0,

                "Estimated_Savings_Percentage":
                    0,

                "Benchmark_Resource_Count":
                    0,

                "Recommendation":
                    "Service category is not mapped.",

                "Recommendation_Confidence":
                    "LOW"
            })

            continue

        # ----------------------------------------------------
        # Find comparable providers
        # ----------------------------------------------------

        comparable = benchmarks[
            benchmarks[
                "Service_Category"
            ]
            ==
            service_category
        ].copy()

        # ----------------------------------------------------
        # Need at least 2 providers
        # ----------------------------------------------------

        if len(comparable) < 2:

            results.append({

                "Account_ID":
                    row["Account_ID"],

                "Current_Provider":
                    current_provider,

                "Current_Service":
                    service,

                "Service_Category":
                    service_category,

                "Region":
                    region,

                "Usage_Hours":
                    usage_hours,

                "Current_Monthly_Cost":
                    round(
                        current_cost,
                        2
                    ),

                "Current_Cost_Per_Hour":
                    round(
                        current_cost_per_hour,
                        4
                    ),

                "Recommended_Provider":
                    "No Recommendation",

                "Alternative_Cost_Per_Hour":
                    current_cost_per_hour,

                "Estimated_Alternative_Cost":
                    current_cost,

                "Estimated_Monthly_Savings":
                    0,

                "Estimated_Savings_Percentage":
                    0,

                "Benchmark_Resource_Count":
                    0,

                "Recommendation":
                    "Insufficient cross-provider "
                    "benchmark data.",

                "Recommendation_Confidence":
                    "LOW"
            })

            continue

        # ----------------------------------------------------
        # Find alternatives
        # ----------------------------------------------------

        alternatives = comparable[
            comparable[
                "Cloud_Provider"
            ]
            != current_provider
        ].copy()

        if alternatives.empty:

            results.append({

                "Account_ID":
                    row["Account_ID"],

                "Current_Provider":
                    current_provider,

                "Current_Service":
                    service,

                "Service_Category":
                    service_category,

                "Region":
                    region,

                "Usage_Hours":
                    usage_hours,

                "Current_Monthly_Cost":
                    round(
                        current_cost,
                        2
                    ),

                "Current_Cost_Per_Hour":
                    round(
                        current_cost_per_hour,
                        4
                    ),

                "Recommended_Provider":
                    "No Recommendation",

                "Alternative_Cost_Per_Hour":
                    current_cost_per_hour,

                "Estimated_Alternative_Cost":
                    current_cost,

                "Estimated_Monthly_Savings":
                    0,

                "Estimated_Savings_Percentage":
                    0,

                "Benchmark_Resource_Count":
                    0,

                "Recommendation":
                    "No alternative provider "
                    "benchmark available.",

                "Recommendation_Confidence":
                    "LOW"
            })

            continue

        # ----------------------------------------------------
        # Cheapest alternative
        # ----------------------------------------------------

        best_alternative = (
            alternatives
            .sort_values(
                "Median_Cost_Per_Hour"
            )
            .iloc[0]
        )

        recommended_provider = (
            best_alternative[
                "Cloud_Provider"
            ]
        )

        alternative_cost_per_hour = (
            best_alternative[
                "Median_Cost_Per_Hour"
            ]
        )

        benchmark_count = int(
            best_alternative[
                "Resource_Count"
            ]
        )

        # ----------------------------------------------------
        # Estimate alternative cost
        # ----------------------------------------------------

        estimated_alternative_cost = (
            alternative_cost_per_hour
            *
            usage_hours
        )

        # ----------------------------------------------------
        # Calculate savings
        # ----------------------------------------------------

        estimated_savings = max(
            0,
            current_cost
            -
            estimated_alternative_cost
        )

        if current_cost > 0:

            savings_percentage = (
                estimated_savings
                /
                current_cost
                *
                100
            )

        else:

            savings_percentage = 0

        # ----------------------------------------------------
        # Recommendation logic
        # ----------------------------------------------------

        if savings_percentage >= 15:

            recommendation = (
                f"Consider {recommended_provider} "
                f"for the {service_category} workload. "
                f"The observed median cost per hour "
                f"is lower for this provider."
            )

            if benchmark_count >= 10:

                confidence = "HIGH"

            else:

                confidence = "MEDIUM"

        elif savings_percentage >= 5:

            recommendation = (
                f"{recommended_provider} shows a "
                f"moderate observed cost advantage "
                f"for this {service_category} workload."
            )

            if benchmark_count >= 10:

                confidence = "MEDIUM"

            else:

                confidence = "LOW"

        else:

            recommended_provider = (
                current_provider
            )

            alternative_cost_per_hour = (
                current_cost_per_hour
            )

            estimated_alternative_cost = (
                current_cost
            )

            estimated_savings = 0

            savings_percentage = 0

            recommendation = (
                "No meaningful cross-provider "
                "cost advantage identified."
            )

            confidence = "LOW"

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append({

            "Account_ID":
                row["Account_ID"],

            "Current_Provider":
                current_provider,

            "Current_Service":
                service,

            "Service_Category":
                service_category,

            "Region":
                region,

            "Usage_Hours":
                usage_hours,

            "Current_Monthly_Cost":
                round(
                    current_cost,
                    2
                ),

            "Current_Cost_Per_Hour":
                round(
                    current_cost_per_hour,
                    4
                ),

            "Recommended_Provider":
                recommended_provider,

            "Alternative_Cost_Per_Hour":
                round(
                    alternative_cost_per_hour,
                    4
                ),

            "Estimated_Alternative_Cost":
                round(
                    estimated_alternative_cost,
                    2
                ),

            "Estimated_Monthly_Savings":
                round(
                    estimated_savings,
                    2
                ),

            "Estimated_Savings_Percentage":
                round(
                    savings_percentage,
                    2
                ),

            "Benchmark_Resource_Count":
                benchmark_count,

            "Recommendation":
                recommendation,

            "Recommendation_Confidence":
                confidence
        })

    return pd.DataFrame(
        results
    )


# ============================================================
# RUN ENGINE
# ============================================================

def run_provider_recommendation():

    print("=" * 70)

    print(
        "DATA-DRIVEN CLOUD PROVIDER "
        "RECOMMENDATION ENGINE"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_data()

    print(
        f"Records loaded: {len(df)}"
    )

    # --------------------------------------------------------
    # Map equivalent services
    # --------------------------------------------------------

    df = map_service_categories(
        df
    )

    print(
        "Service equivalence mapping completed."
    )

    print()
    print(
        "Service Categories:"
    )

    print(
        df[
            [
                "Service",
                "Service_Category"
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "Service_Category"
        )
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Cost efficiency
    # --------------------------------------------------------

    df = calculate_cost_efficiency(
        df
    )

    print()
    print(
        "Cost-per-hour efficiency calculated."
    )

    # --------------------------------------------------------
    # Benchmarks
    # --------------------------------------------------------

    benchmarks = (
        calculate_provider_benchmarks(
            df
        )
    )

    print(
        "Cross-provider benchmarks calculated."
    )

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    recommendations = (
        generate_recommendations(
            df,
            benchmarks
        )
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    recommendations = (
        recommendations
        .sort_values(
            "Estimated_Monthly_Savings",
            ascending=False
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        "results",
        exist_ok=True
    )

    recommendations.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # MIGRATION CANDIDATES
    # ========================================================

    migration_candidates = (
        recommendations[
            (
                recommendations[
                    "Recommended_Provider"
                ]
                !=
                recommendations[
                    "Current_Provider"
                ]
            )
            &
            (
                recommendations[
                    "Estimated_Monthly_Savings"
                ]
                > 0
            )
        ]
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    total_savings = (
        migration_candidates[
            "Estimated_Monthly_Savings"
        ].sum()
    )

    annual_savings = (
        total_savings * 12
    )

    print()
    print(
        "Provider Recommendation Distribution:"
    )

    print(
        recommendations[
            "Recommended_Provider"
        ].value_counts()
    )

    print()
    print(
        "Recommendation Confidence:"
    )

    print(
        recommendations[
            "Recommendation_Confidence"
        ].value_counts()
    )

    print()
    print(
        f"Migration Candidates: "
        f"{len(migration_candidates)}"
    )

    print(
        f"Potential Monthly Savings: "
        f"${total_savings:,.2f}"
    )

    print(
        f"Potential Annual Savings: "
        f"${annual_savings:,.2f}"
    )

    # ========================================================
    # TOP 10
    # ========================================================

    print()
    print("=" * 70)

    print(
        "TOP 10 PROVIDER OPTIMIZATION OPPORTUNITIES"
    )

    print("=" * 70)

    if not migration_candidates.empty:

        top_columns = [

            "Account_ID",

            "Current_Provider",

            "Current_Service",

            "Service_Category",

            "Current_Monthly_Cost",

            "Current_Cost_Per_Hour",

            "Recommended_Provider",

            "Alternative_Cost_Per_Hour",

            "Estimated_Alternative_Cost",

            "Estimated_Monthly_Savings",

            "Estimated_Savings_Percentage",

            "Recommendation_Confidence"
        ]

        print(
            migration_candidates[
                top_columns
            ]
            .head(10)
            .to_string(
                index=False
            )
        )

    else:

        print(
            "No provider migration opportunities "
            "identified."
        )

    print()
    print(
        f"Results saved to: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_provider_recommendation()