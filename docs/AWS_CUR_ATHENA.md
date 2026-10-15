# AWS CUR 2.0: Glue Catalog and Athena Query Layer

## Purpose

The CUR 2.0 export already delivers Parquet files to the project's S3 data lake. This optional Terraform layer makes those files discoverable through Glue Data Catalog and queryable with Athena, without loading them into another database.

## What Terraform declares

- A Glue Catalog database named cloud_cost_optimization_cur.
- A Glue crawler aimed at raw/aws-cur/cloud-cost-optimization-cur/data/. The crawler has no automatic schedule; start it manually when you decide to refresh the catalog.
- A dedicated Athena workgroup with encrypted query results and a 50 MiB scan cutoff for each query.
- The Glue role's scoped data-lake permissions, including bucket-location lookup.

**These are declarations only until Terraform is applied.** The existing project was checked and had no Glue database/crawler and only the default Athena workgroup as of the last AWS inventory. Do not run terraform apply blindly. Review state and plan first.

## Deployment review sequence

From PowerShell:

~~~powershell
Set-Location "$env:USERPROFILE\OneDrive\Desktop\BigData\cloud-cost-optimization\terraform"
terraform fmt -check -recursive
terraform validate
terraform plan
~~~

Before considering terraform apply, confirm the plan proposes only the intended Glue database, crawler, Athena workgroup, query-results prefix, and Glue IAM permission. If existing resources show replacements, unrelated destroys, a state mismatch, or unexpected changes, stop and reconcile state before applying. Do not commit Terraform state or .tfvars secrets.

A Glue crawler and Athena queries may incur charges when run. The workgroup's scan cutoff is intentionally conservative; it is not a monthly account budget and may cause large queries to fail instead of scanning more data.

## After resources are deployed

1. In AWS Glue, start the cloud-cost-optimization-cur-crawler crawler manually.
2. Wait for a successful crawler run and check the generated table and BILLING_PERIOD partition.
3. In Athena, select the cloud-cost-optimization-cur-analytics workgroup and cloud_cost_optimization_cur database.
4. Replace <generated_table_name> in the example below with the actual crawler-generated table name.

## Example SQL: reported service costs

~~~sql
SELECT
    product_servicecode,
    line_item_currency_code,
    SUM(TRY_CAST(line_item_unblended_cost AS DOUBLE)) AS reported_unblended_cost,
    COUNT(*) AS line_items
FROM "cloud_cost_optimization_cur"."<generated_table_name>"
WHERE line_item_currency_code = 'USD'
  AND line_item_line_item_type IS NOT NULL
GROUP BY product_servicecode, line_item_currency_code
ORDER BY reported_unblended_cost DESC
LIMIT 20;
~~~

This query reports line-item unblended cost for USD rows only. It does not convert currencies or guarantee that the sum equals the final invoice.

## Example SQL: daily cost trend

~~~sql
SELECT
    CAST(TRY_CAST(line_item_usage_start_date AS TIMESTAMP) AS DATE) AS usage_day,
    line_item_currency_code,
    SUM(TRY_CAST(line_item_unblended_cost AS DOUBLE)) AS reported_unblended_cost,
    COUNT(*) AS line_items
FROM "cloud_cost_optimization_cur"."<generated_table_name>"
WHERE line_item_currency_code = 'USD'
  AND line_item_usage_start_date IS NOT NULL
GROUP BY CAST(TRY_CAST(line_item_usage_start_date AS TIMESTAMP) AS DATE), line_item_currency_code
ORDER BY usage_day;
~~~

The October billing period can be incomplete. Compare like-for-like time windows before interpreting a month-over-month change. CUR data also includes different line-item types (usage, credits, discounts, taxes and adjustments); decide which types are appropriate for a particular FinOps metric.

## Relationship to the Streamlit Cost Copilot

The dashboard's live view currently reads a small set of recent CUR Parquet files directly from S3 and computes charts, outlier candidates, and chatbot context locally. Athena is a separate queryable analytics path for reproducible SQL and larger datasets; it is not yet wired into the dashboard's runtime query path. Do not claim Athena is operational until the Terraform resources are deployed, a crawler succeeds, and a query result is verified.
