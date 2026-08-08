import pandas as pd
import random
from datetime import date, timedelta

random.seed(42)

providers = {
    "AWS": ["EC2", "S3", "RDS", "Lambda"],
    "Azure": ["Virtual Machines", "Blob Storage", "Azure SQL", "Functions"],
    "GCP": ["Compute Engine", "Cloud Storage", "Cloud SQL", "Cloud Functions"]
}

regions = {
    "AWS": ["us-east-1", "us-west-2", "ap-south-1"],
    "Azure": ["eastus", "westus", "centralindia"],
    "GCP": ["us-central1", "us-west1", "asia-south1"]
}

start_date = date(2026, 1, 1)

rows = []

for i in range(500):
    provider = random.choice(list(providers.keys()))
    service = random.choice(providers[provider])
    region = random.choice(regions[provider])

    usage_date = start_date + timedelta(days=random.randint(0, 89))
    usage_hours = random.randint(50, 720)
    data_transfer = round(random.uniform(10, 1000), 2)
    storage = round(random.uniform(20, 2000), 2)

    monthly_cost = round(
        usage_hours * random.uniform(0.08, 0.45)
        + data_transfer * random.uniform(0.01, 0.08)
        + storage * random.uniform(0.01, 0.05),
        2
    )

    rows.append([
        f"ACC-{random.randint(100, 149)}",
        provider,
        service,
        region,
        usage_date,
        usage_hours,
        data_transfer,
        storage,
        monthly_cost
    ])

df = pd.DataFrame(rows, columns=[
    "Account_ID",
    "Cloud_Provider",
    "Service",
    "Region",
    "Usage_Date",
    "Usage_Hours",
    "Data_Transfer_GB",
    "Storage_GB",
    "Monthly_Cost"
])

output_path = "data/raw/cloud_cost_data.csv"
df.to_csv(output_path, index=False)

print(f"Dataset created successfully: {output_path}")
print(f"Rows: {len(df)}")
print(df.head())