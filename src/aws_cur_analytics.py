"""Read-only access to recent AWS CUR 2.0 Parquet data already stored in S3.

This does not create AWS resources or query/write to the user's database.
It reads only the latest billing-period partitions from the configured CUR export.
"""
from __future__ import annotations

import io
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import boto3
from botocore.config import Config
import pandas as pd


DEFAULT_CUR_PREFIX = "raw/aws-cur/cloud-cost-optimization-cur/data/"


def parse_billing_period(key: str) -> str | None:
    """Return YYYY-MM from a CUR object key with a BILLING_PERIOD partition."""
    match = re.search(r"(?:^|/)BILLING_PERIOD=(\d{4}-\d{2})(?:/|$)", key)
    return match.group(1) if match else None


def select_recent_objects(
    objects: list[dict[str, Any]], periods_to_keep: int = 2
) -> list[dict[str, Any]]:
    """Keep Parquet objects for the newest billing periods represented in a listing."""
    if periods_to_keep < 1:
        raise ValueError("periods_to_keep must be at least 1")

    valid = []
    for obj in objects:
        key = str(obj.get("Key", ""))
        period = parse_billing_period(key)
        if key.lower().endswith(".parquet") and period:
            valid.append({**obj, "Billing_Period": period})

    periods = sorted({obj["Billing_Period"] for obj in valid}, reverse=True)
    keep = set(periods[:periods_to_keep])

    return sorted(
        [obj for obj in valid if obj["Billing_Period"] in keep],
        key=lambda obj: (obj["Billing_Period"], str(obj.get("LastModified", "")), obj["Key"]),
        reverse=True,
    )


def prepare_cur_frame(frame: pd.DataFrame, billing_period: str) -> pd.DataFrame:
    """Normalize columns and create safe, display-ready currency/service columns."""
    result = frame.copy()
    result.columns = [str(column).strip().lower() for column in result.columns]

    if "line_item_unblended_cost" not in result.columns:
        raise ValueError(
            "CUR Parquet schema does not include line_item_unblended_cost. "
            "Check the Billing Data Export query/schema."
        )

    result["line_item_unblended_cost"] = pd.to_numeric(
        result["line_item_unblended_cost"], errors="coerce"
    ).fillna(0.0)

    if "line_item_currency_code" in result.columns:
        result["Currency"] = (
            result["line_item_currency_code"].fillna("Unknown").astype(str).str.strip()
        )
        result.loc[result["Currency"].isin(["", "nan", "None"]), "Currency"] = "Unknown"
    else:
        result["Currency"] = "Unknown"

    service_source = None
    if "product_servicecode" in result.columns:
        service_source = result["product_servicecode"].astype("string")
    if "line_item_product_code" in result.columns:
        product_source = result["line_item_product_code"].astype("string")
        service_source = product_source if service_source is None else service_source.fillna(product_source)

    if service_source is None:
        result["Service"] = "Unknown"
    else:
        result["Service"] = service_source.fillna("Unknown").astype(str).str.strip()
        result.loc[result["Service"].isin(["", "nan", "None", "<NA>"]), "Service"] = "Unknown"

    result["Billing_Period"] = billing_period
    return result


def summarize_cur_data(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return period/currency and service/currency summaries without mixing currencies."""
    required = {"Billing_Period", "Currency", "Service", "line_item_unblended_cost"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Prepared CUR data is missing columns: {', '.join(sorted(missing))}")

    work = frame.copy()
    work["line_item_unblended_cost"] = pd.to_numeric(
        work["line_item_unblended_cost"], errors="coerce"
    ).fillna(0.0)

    monthly = (
        work.groupby(["Billing_Period", "Currency"], dropna=False, as_index=False)
        .agg(
            Reported_Unblended_Cost=("line_item_unblended_cost", "sum"),
            Line_Items=("line_item_unblended_cost", "size"),
        )
        .sort_values(["Billing_Period", "Currency"], ascending=[False, True])
        .reset_index(drop=True)
    )

    services = (
        work.groupby(["Service", "Currency"], dropna=False, as_index=False)
        .agg(
            Reported_Unblended_Cost=("line_item_unblended_cost", "sum"),
            Line_Items=("line_item_unblended_cost", "size"),
        )
        .sort_values(["Currency", "Reported_Unblended_Cost"], ascending=[True, False])
        .reset_index(drop=True)
    )

    return {"monthly": monthly, "services": services}


def analyze_cur_data(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create operationally useful summaries directly from real CUR line items.

    Costs are always grouped by currency. Outliers are review candidates, not
    automatically waste or guaranteed savings.
    """
    required = {"Billing_Period", "Currency", "Service", "line_item_unblended_cost"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            f"Prepared CUR data is missing columns: {', '.join(sorted(missing))}"
        )

    work = frame.copy()
    work["line_item_unblended_cost"] = pd.to_numeric(
        work["line_item_unblended_cost"], errors="coerce"
    ).fillna(0.0)

    # Normalize optional CUR dimensions for dashboard display.
    if "line_item_line_item_type" in work.columns:
        work["Line_Item_Type"] = (
            work["line_item_line_item_type"].fillna("Unknown").astype(str)
        )
    else:
        work["Line_Item_Type"] = "Unknown"

    if "line_item_usage_type" in work.columns:
        work["Usage_Type"] = work["line_item_usage_type"].fillna("Unknown").astype(str)
    else:
        work["Usage_Type"] = "Unknown"

    if "line_item_usage_start_date" in work.columns:
        parsed_dates = pd.to_datetime(
            work["line_item_usage_start_date"], errors="coerce", utc=True
        )
        work["Usage_Date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    else:
        work["Usage_Date"] = pd.NA

    summaries = summarize_cur_data(work)

    daily_source = work.dropna(subset=["Usage_Date"])
    if not daily_source.empty:
        daily = (
            daily_source.groupby(["Usage_Date", "Currency"], dropna=False, as_index=False)
            .agg(
                Reported_Unblended_Cost=("line_item_unblended_cost", "sum"),
                Line_Items=("line_item_unblended_cost", "size"),
            )
            .sort_values(["Usage_Date", "Currency"])
            .reset_index(drop=True)
        )
    else:
        daily = pd.DataFrame(
            columns=["Usage_Date", "Currency", "Reported_Unblended_Cost", "Line_Items"]
        )

    line_item_types = (
        work.groupby(["Line_Item_Type", "Currency"], dropna=False, as_index=False)
        .agg(
            Reported_Unblended_Cost=("line_item_unblended_cost", "sum"),
            Line_Items=("line_item_unblended_cost", "size"),
        )
        .sort_values(["Currency", "Reported_Unblended_Cost"], ascending=[True, False])
        .reset_index(drop=True)
    )

    # Robust IQR outliers computed separately per currency and positive line-item
    # costs only, preventing negative credits/refunds from distorting the threshold.
    anomaly_rows = []
    for currency, group in work.groupby("Currency", dropna=False):
        positive = group.loc[group["line_item_unblended_cost"] > 0].copy()
        if len(positive) < 4:
            continue
        q1 = positive["line_item_unblended_cost"].quantile(0.25)
        q3 = positive["line_item_unblended_cost"].quantile(0.75)
        upper = q3 + 1.5 * (q3 - q1)
        flagged = positive.loc[positive["line_item_unblended_cost"] > upper].copy()
        if flagged.empty:
            continue
        flagged["Outlier_Upper_Bound"] = upper
        flagged["Outlier_Flag"] = "Review high-cost line item"
        anomaly_rows.append(flagged)

    if anomaly_rows:
        anomalies = pd.concat(anomaly_rows, ignore_index=True, sort=False)
        keep_columns = [
            column for column in [
                "Billing_Period",
                "Usage_Date",
                "Currency",
                "Service",
                "Line_Item_Type",
                "Usage_Type",
                "line_item_unblended_cost",
                "Outlier_Upper_Bound",
                "Outlier_Flag",
            ] if column in anomalies.columns
        ]
        anomalies = anomalies[keep_columns].sort_values(
            "line_item_unblended_cost", ascending=False
        ).head(100).reset_index(drop=True)
    else:
        anomalies = pd.DataFrame(
            columns=[
                "Billing_Period", "Usage_Date", "Currency", "Service",
                "Line_Item_Type", "Usage_Type", "line_item_unblended_cost",
                "Outlier_Upper_Bound", "Outlier_Flag",
            ]
        )

    return {
        **summaries,
        "daily": daily,
        "line_item_types": line_item_types,
        "high_cost_line_items": anomalies,
    }


def load_recent_cur_data(
    *,
    session=None,
    bucket: str | None = None,
    prefix: str | None = None,
    periods_to_keep: int = 2,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Download recent CUR Parquet files from S3 using the standard boto3 credential chain.

    Set CLOUD_COST_AWS_CUR_BUCKET to override automatic bucket discovery. Otherwise,
    the expected bucket name is derived from the AWS account returned by STS:
    cloud-cost-optimization-<account-id>.
    """
    region = (
        os.environ.get("CLOUD_COST_AWS_REGION")
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )
    session = session or boto3.Session(region_name=region)
    prefix = (prefix or os.environ.get("CLOUD_COST_AWS_CUR_PREFIX") or DEFAULT_CUR_PREFIX).lstrip("/")

    if not bucket:
        bucket = os.environ.get("CLOUD_COST_AWS_CUR_BUCKET")
    if not bucket:
        account_id = session.client("sts", region_name=region).get_caller_identity()["Account"]
        bucket = f"cloud-cost-optimization-{account_id}"

    s3 = session.client(
        "s3",
        region_name=region,
        config=Config(
            connect_timeout=4,
            read_timeout=20,
            retries={"mode": "standard", "total_max_attempts": 2},
            max_pool_connections=10,
        ),
    )
    paginator = s3.get_paginator("list_objects_v2")
    objects = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects.extend(page.get("Contents", []))

    selected = select_recent_objects(objects, periods_to_keep=periods_to_keep)
    if not selected:
        raise FileNotFoundError(
            f"No CUR Parquet files with BILLING_PERIOD partitions were found under "
            f"s3://{bucket}/{prefix}. Check the bucket, prefix, and AWS profile."
        )

    def read_cur_object(obj: dict[str, Any]) -> pd.DataFrame:
        response = s3.get_object(Bucket=bucket, Key=obj["Key"])
        parquet_bytes = response["Body"].read()
        raw = pd.read_parquet(io.BytesIO(parquet_bytes), engine="pyarrow")
        return prepare_cur_frame(raw, obj["Billing_Period"])

    # Download and parse independent Parquet objects concurrently; preserve object order.
    worker_count = min(8, len(selected))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        frames = list(executor.map(read_cur_object, selected))

    combined = pd.concat(frames, ignore_index=True, sort=False)
    last_modified = max(
        (obj.get("LastModified") for obj in selected if obj.get("LastModified") is not None),
        default=None,
    )
    metadata = {
        "object_count": len(selected),
        "periods": sorted({obj["Billing_Period"] for obj in selected}),
        "last_object_modified_utc": (
            last_modified.isoformat() if isinstance(last_modified, datetime) else None
        ),
    }
    return combined, metadata
