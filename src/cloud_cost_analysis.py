from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "raw" / "cloud_cost_data.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "cloud_cost_analysis.csv"


def analyze_costs(df: pd.DataFrame) -> pd.DataFrame:
    """Add cost-per-hour, high-cost flags, and basic service recommendations."""
    required_columns = {"Monthly_Cost", "Usage_Hours", "Service"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")

    result = df.copy()
    usage_hours = pd.to_numeric(result["Usage_Hours"], errors="raise").replace(0, 1)
    monthly_cost = pd.to_numeric(result["Monthly_Cost"], errors="raise")

    result["Cost_Per_Hour"] = monthly_cost / usage_hours
    cost_threshold = monthly_cost.quantile(0.90)
    result["Optimization_Flag"] = monthly_cost.apply(
        lambda value: "High Cost" if value >= cost_threshold else "Normal"
    )

    def get_recommendation(row):
        if row["Optimization_Flag"] != "High Cost":
            return "No Immediate Action"

        service = str(row["Service"])
        if service in ["EC2", "Virtual Machines", "Compute Engine"]:
            return "Review Compute Usage"
        if service in ["S3", "Blob Storage", "Cloud Storage"]:
            return "Review Storage Usage"
        if service in ["RDS", "Azure SQL", "Cloud SQL"]:
            return "Review Database Usage"
        return "Review Service Usage"

    result["Recommendation"] = result.apply(get_recommendation, axis=1)
    return result


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}. Run from any directory; "
            "the path is resolved relative to the project."
        )

    df = pd.read_csv(INPUT_FILE)
    analyzed = analyze_costs(df)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    analyzed.to_csv(OUTPUT_FILE, index=False)

    print("Cloud cost analysis completed.")
    print(f"Records analyzed: {len(analyzed):,}")
    print(f"Total monthly cost: \${analyzed['Monthly_Cost'].sum():,.2f}")
    print(
        "High-cost records: "
        f"{(analyzed['Optimization_Flag'] == 'High Cost').sum():,}"
    )
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
