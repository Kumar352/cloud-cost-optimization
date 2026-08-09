import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# CLOUD COST DATASET GENERATOR
# ============================================================

OUTPUT_FILE = "data/raw/cloud_cost_data.csv"

TOTAL_RECORDS = 15000

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ============================================================
# CLOUD PROVIDER / SERVICE CONFIGURATION
# ============================================================

SERVICE_CONFIG = {

    "AWS": {
        "EC2": {
            "category": "Compute",
            "regions": [
                "us-east-1",
                "us-west-2",
                "ap-south-1",
                "eu-west-1"
            ],
            "base_rate": 0.62
        },

        "RDS": {
            "category": "Database",
            "regions": [
                "us-east-1",
                "us-west-2",
                "ap-south-1",
                "eu-west-1"
            ],
            "base_rate": 0.48
        },

        "S3": {
            "category": "Storage",
            "regions": [
                "us-east-1",
                "us-west-2",
                "ap-south-1",
                "eu-west-1"
            ],
            "base_rate": 0.42
        },

        "Lambda": {
            "category": "Serverless",
            "regions": [
                "us-east-1",
                "us-west-2",
                "ap-south-1",
                "eu-west-1"
            ],
            "base_rate": 0.40
        }
    },

    "Azure": {
        "Virtual Machines": {
            "category": "Compute",
            "regions": [
                "eastus",
                "westus",
                "centralindia",
                "westeurope"
            ],
            "base_rate": 0.57
        },

        "Azure SQL": {
            "category": "Database",
            "regions": [
                "eastus",
                "westus",
                "centralindia",
                "westeurope"
            ],
            "base_rate": 0.53
        },

        "Blob Storage": {
            "category": "Storage",
            "regions": [
                "eastus",
                "westus",
                "centralindia",
                "westeurope"
            ],
            "base_rate": 0.39
        },

        "Functions": {
            "category": "Serverless",
            "regions": [
                "eastus",
                "westus",
                "centralindia",
                "westeurope"
            ],
            "base_rate": 0.37
        }
    },

    "GCP": {
        "Compute Engine": {
            "category": "Compute",
            "regions": [
                "us-west1",
                "us-central1",
                "asia-south1",
                "europe-west1"
            ],
            "base_rate": 0.46
        },

        "Cloud SQL": {
            "category": "Database",
            "regions": [
                "us-west1",
                "us-central1",
                "asia-south1",
                "europe-west1"
            ],
            "base_rate": 0.38
        },

        "Cloud Storage": {
            "category": "Storage",
            "regions": [
                "us-west1",
                "us-central1",
                "asia-south1",
                "europe-west1"
            ],
            "base_rate": 0.41
        },

        "Cloud Functions": {
            "category": "Serverless",
            "regions": [
                "us-west1",
                "us-central1",
                "asia-south1",
                "europe-west1"
            ],
            "base_rate": 0.34
        }
    }
}


# ============================================================
# GENERATE RECORD
# ============================================================

def generate_record(index):

    provider = random.choice(
        list(SERVICE_CONFIG.keys())
    )

    service = random.choice(
        list(
            SERVICE_CONFIG[
                provider
            ].keys()
        )
    )

    config = (
        SERVICE_CONFIG[
            provider
        ][
            service
        ]
    )

    region = random.choice(
        config["regions"]
    )

    category = config[
        "category"
    ]

    # --------------------------------------------------------
    # Usage
    # --------------------------------------------------------

    usage_hours = random.randint(
        40,
        720
    )

    # --------------------------------------------------------
    # Data transfer
    # --------------------------------------------------------

    data_transfer_gb = round(
        np.random.lognormal(
            mean=5.2,
            sigma=0.65
        ),
        2
    )

    data_transfer_gb = min(
        max(
            data_transfer_gb,
            10
        ),
        2000
    )

    # --------------------------------------------------------
    # Storage
    # --------------------------------------------------------

    storage_gb = round(
        np.random.lognormal(
            mean=6.0,
            sigma=0.75
        ),
        2
    )

    storage_gb = min(
        max(
            storage_gb,
            20
        ),
        5000
    )

    # --------------------------------------------------------
    # Service-specific cost behavior
    # --------------------------------------------------------

    if category == "Compute":

        usage_multiplier = 1.00

        transfer_multiplier = 0.006

        storage_multiplier = 0.015

    elif category == "Database":

        usage_multiplier = 1.15

        transfer_multiplier = 0.008

        storage_multiplier = 0.020

    elif category == "Storage":

        usage_multiplier = 0.30

        transfer_multiplier = 0.004

        storage_multiplier = 0.025

    else:

        usage_multiplier = 0.70

        transfer_multiplier = 0.005

        storage_multiplier = 0.010

    # --------------------------------------------------------
    # Base cost
    # --------------------------------------------------------

    usage_cost = (
        usage_hours
        * config["base_rate"]
        * usage_multiplier
    )

    transfer_cost = (
        data_transfer_gb
        * transfer_multiplier
    )

    storage_cost = (
        storage_gb
        * storage_multiplier
    )

    monthly_cost = (
        usage_cost
        +
        transfer_cost
        +
        storage_cost
    )

    # --------------------------------------------------------
    # Realistic cost variation
    # --------------------------------------------------------

    cost_variation = np.random.normal(
        loc=1.0,
        scale=0.12
    )

    monthly_cost *= cost_variation

    # --------------------------------------------------------
    # Occasional expensive resources
    # --------------------------------------------------------

    high_cost_probability = 0.10

    if random.random() < high_cost_probability:

        monthly_cost *= random.uniform(
            1.35,
            2.10
        )

    # --------------------------------------------------------
    # Occasional low-utilization resources
    # --------------------------------------------------------

    if random.random() < 0.25:

        usage_hours = random.randint(
            20,
            250
        )

    # --------------------------------------------------------
    # Prevent unrealistic values
    # --------------------------------------------------------

    monthly_cost = max(
        monthly_cost,
        5.0
    )

    # --------------------------------------------------------
    # Usage date
    # --------------------------------------------------------

    start_date = datetime(
        2026,
        1,
        1
    )

    usage_date = (
        start_date
        +
        timedelta(
            days=random.randint(
                0,
                181
            )
        )
    )

    # --------------------------------------------------------
    # Account
    # --------------------------------------------------------

    account_number = (
        100
        +
        (index % 50)
    )

    account_id = (
        f"ACC-{account_number}"
    )

    return {

        "Account_ID":
            account_id,

        "Cloud_Provider":
            provider,

        "Service":
            service,

        "Region":
            region,

        "Usage_Date":
            usage_date.strftime(
                "%Y-%m-%d"
            ),

        "Usage_Hours":
            usage_hours,

        "Data_Transfer_GB":
            round(
                data_transfer_gb,
                2
            ),

        "Storage_GB":
            round(
                storage_gb,
                2
            ),

        "Monthly_Cost":
            round(
                monthly_cost,
                2
            )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "CLOUD COST OPTIMIZATION DATASET GENERATOR"
    )

    print(
        "=" * 70
    )

    print(
        f"Generating {TOTAL_RECORDS:,} records..."
    )

    records = []

    for index in range(
        TOTAL_RECORDS
    ):

        records.append(
            generate_record(
                index
            )
        )

    df = pd.DataFrame(
        records
    )

    # --------------------------------------------------------
    # Sort by usage date
    # --------------------------------------------------------

    df = df.sort_values(
        "Usage_Date"
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    output_directory = os.path.dirname(
        OUTPUT_FILE
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save dataset
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print(
        "Dataset generation completed."
    )

    print(
        f"Records generated: "
        f"{len(df):,}"
    )

    print(
        f"Total monthly cloud cost: "
        f"${df['Monthly_Cost'].sum():,.2f}"
    )

    print(
        f"Average monthly cost: "
        f"${df['Monthly_Cost'].mean():,.2f}"
    )

    print(
        f"Minimum monthly cost: "
        f"${df['Monthly_Cost'].min():,.2f}"
    )

    print(
        f"Maximum monthly cost: "
        f"${df['Monthly_Cost'].max():,.2f}"
    )

    print()

    print(
        "Cloud Provider Distribution:"
    )

    print(
        df[
            "Cloud_Provider"
        ].value_counts()
    )

    print()

    print(
        "Service Distribution:"
    )

    print(
        df[
            "Service"
        ].value_counts()
    )

    print()

    print(
        f"Dataset saved to: "
        f"{OUTPUT_FILE}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()