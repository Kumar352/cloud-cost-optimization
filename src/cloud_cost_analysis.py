import pandas as pd

INPUT_FILE = "../data/raw/cloud_cost_data.csv"
OUTPUT_FILE = "../data/processed/cloud_cost_analysis.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    df["Cost_Per_Hour"] = df["Monthly_Cost"] / df["Usage_Hours"]

    cost_threshold = df["Monthly_Cost"].quantile(0.90)

    df["Optimization_Flag"] = df["Monthly_Cost"].apply(
        lambda x: "High Cost" if x >= cost_threshold else "Normal"
    )

    def get_recommendation(row):
        if row["Optimization_Flag"] != "High Cost":
            return "No Immediate Action"

        if row["Service"] in ["EC2", "Virtual Machines", "Compute Engine"]:
            return "Review Compute Usage"

        if row["Service"] in ["S3", "Blob Storage", "Cloud Storage"]:
            return "Review Storage Usage"

        if row["Service"] in ["RDS", "Azure SQL", "Cloud SQL"]:
            return "Review Database Usage"

        return "Review Service Usage"

    df["Recommendation"] = df.apply(get_recommendation, axis=1)

    df.to_csv(OUTPUT_FILE, index=False)

    print("Cloud cost analysis completed.")
    print(f"Records analyzed: {len(df)}")
    print(f"Total monthly cost: ${df['Monthly_Cost'].sum():,.2f}")
    print(f"High-cost records: {(df['Optimization_Flag'] == 'High Cost').sum()}")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()