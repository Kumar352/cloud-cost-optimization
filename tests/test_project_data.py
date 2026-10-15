import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import pytest

from src.cloud_cost_analysis import analyze_costs

RAW_DATA = PROJECT_ROOT / "data" / "raw" / "cloud_cost_data.csv"


def test_demo_dataset_has_expected_schema_and_valid_costs():
    assert RAW_DATA.is_file(), f"Expected dataset is missing: {RAW_DATA}"
    df = pd.read_csv(RAW_DATA)

    expected = {
        "Account_ID",
        "Cloud_Provider",
        "Service",
        "Region",
        "Usage_Date",
        "Usage_Hours",
        "Data_Transfer_GB",
        "Storage_GB",
        "Monthly_Cost",
    }
    assert expected.issubset(df.columns)
    assert len(df) >= 1000
    assert pd.to_numeric(df["Monthly_Cost"], errors="coerce").notna().all()
    assert (df["Monthly_Cost"] >= 0).all()
    assert df["Cloud_Provider"].isin(["AWS", "Azure", "GCP"]).all()


def test_analysis_adds_flags_recommendations_and_handles_zero_usage():
    sample = pd.DataFrame(
        {
            "Service": ["EC2", "S3", "RDS", "Other", "EC2"],
            "Usage_Hours": [0, 10, 20, 30, 40],
            "Monthly_Cost": [100.0, 20.0, 30.0, 10.0, 50.0],
        }
    )

    analyzed = analyze_costs(sample)

    assert len(analyzed) == len(sample)
    assert {"Cost_Per_Hour", "Optimization_Flag", "Recommendation"}.issubset(
        analyzed.columns
    )
    assert analyzed["Cost_Per_Hour"].notna().all()
    assert analyzed.loc[0, "Cost_Per_Hour"] == pytest.approx(100.0)
    assert "High Cost" in set(analyzed["Optimization_Flag"])
    assert analyzed.loc[0, "Recommendation"] == "Review Compute Usage"
    assert analyzed.loc[1, "Recommendation"] in {
        "Review Storage Usage",
        "No Immediate Action",
    }


def test_analysis_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        analyze_costs(pd.DataFrame({"Monthly_Cost": [12.0]}))


def test_hadoop_output_parser_groups_summary_rows():
    from src.hadoop_output_processor import parse_output

    providers, services, regions = parse_output(
        [
            "PROVIDER|AWS\t100.50",
            "SERVICE|EC2\t70.25",
            "REGION|us-east-1\t100.50",
            "MALFORMED LINE",
            "",
        ]
    )

    assert providers == [{"Cloud_Provider": "AWS", "Monthly_Cost": 100.50}]
    assert services == [{"Service": "EC2", "Monthly_Cost": 70.25}]
    assert regions == [{"Region": "us-east-1", "Monthly_Cost": 100.50}]


def test_summary_csv_matches_current_raw_dataset():
    summary_file = PROJECT_ROOT / "results" / "cost_summary.csv"
    assert summary_file.is_file(), f"Summary CSV is missing: {summary_file}"

    raw_df = pd.read_csv(RAW_DATA)
    summary_df = pd.read_csv(summary_file)
    metrics = dict(zip(summary_df["Metric"], summary_df["Value"]))

    assert int(float(metrics["Total Records Analyzed"])) == len(raw_df)
    assert float(metrics["Total Monthly Cloud Cost"]) == pytest.approx(
        raw_df["Monthly_Cost"].sum(), abs=0.01
    )


def test_cur_billing_period_parser_and_recent_object_selection():
    from src.aws_cur_analytics import parse_billing_period, select_recent_objects

    objects = [
        {"Key": "raw/aws-cur/data/BILLING_PERIOD=2026-08/a.parquet"},
        {"Key": "raw/aws-cur/data/BILLING_PERIOD=2026-09/b.parquet"},
        {"Key": "raw/aws-cur/data/BILLING_PERIOD=2026-10/c.parquet"},
        {"Key": "raw/aws-cur/data/BILLING_PERIOD=2026-10/ignore.csv"},
        {"Key": "raw/aws-cur/data/no-period.parquet"},
    ]

    assert parse_billing_period(objects[2]["Key"]) == "2026-10"
    assert parse_billing_period("raw/aws-cur/data/no-period.parquet") is None
    selected = select_recent_objects(objects, periods_to_keep=2)
    assert {item["Billing_Period"] for item in selected} == {"2026-09", "2026-10"}
    assert len(selected) == 2


def test_cur_prepare_and_summary_preserve_currency_and_period():
    from src.aws_cur_analytics import prepare_cur_frame, summarize_cur_data

    source = pd.DataFrame(
        {
            "line_item_unblended_cost": ["10.25", "4.75", "-1.00"],
            "line_item_currency_code": ["USD", "USD", "USD"],
            "line_item_product_code": ["AmazonEC2", "AmazonS3", "AmazonEC2"],
            "product_servicecode": [
                "Amazon Elastic Compute Cloud",
                "Amazon Simple Storage Service",
                "Amazon Elastic Compute Cloud",
            ],
        }
    )

    prepared = prepare_cur_frame(source, "2026-10")
    summaries = summarize_cur_data(prepared)

    assert prepared["Billing_Period"].eq("2026-10").all()
    assert prepared["Currency"].eq("USD").all()
    assert summaries["monthly"].iloc[0]["Reported_Unblended_Cost"] == pytest.approx(14.0)
    assert set(summaries["services"]["Currency"]) == {"USD"}
    assert summaries["services"].iloc[0]["Service"] == "Amazon Elastic Compute Cloud"


def test_cur_analysis_includes_daily_service_type_and_iqr_review():
    from src.aws_cur_analytics import prepare_cur_frame, analyze_cur_data

    costs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 100.0]
    source = pd.DataFrame(
        {
            "line_item_unblended_cost": costs,
            "line_item_currency_code": ["USD"] * len(costs),
            "line_item_product_code": ["AmazonEC2"] * len(costs),
            "product_servicecode": ["Amazon Elastic Compute Cloud"] * len(costs),
            "line_item_usage_start_date": [
                "2026-10-01T00:00:00Z",
                "2026-10-01T01:00:00Z",
                "2026-10-01T02:00:00Z",
                "2026-10-02T00:00:00Z",
                "2026-10-02T01:00:00Z",
                "2026-10-03T00:00:00Z",
                "2026-10-03T01:00:00Z",
                "2026-10-03T02:00:00Z",
            ],
            "line_item_line_item_type": ["Usage"] * len(costs),
            "line_item_usage_type": ["USE1-BoxUsage"] * len(costs),
        }
    )

    prepared = prepare_cur_frame(source, "2026-10")
    result = analyze_cur_data(prepared)

    assert not result["daily"].empty
    assert result["daily"]["Reported_Unblended_Cost"].sum() == pytest.approx(128.0)
    assert result["line_item_types"]["Line_Items"].sum() == len(costs)
    assert not result["high_cost_line_items"].empty
    assert result["high_cost_line_items"].iloc[0]["line_item_unblended_cost"] == pytest.approx(100.0)
    assert "Billing_Period" in result["monthly"].columns
