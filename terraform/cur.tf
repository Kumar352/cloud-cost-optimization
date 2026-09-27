resource "aws_bcmdataexports_export" "cost_usage" {
  export {
    name        = var.data_export_name
    description = "Real AWS Cost and Usage data for Cloud Cost Optimization Analytics Using Hadoop"

    data_query {
      query_statement = <<-SQL
        SELECT
          identity_line_item_id,
          identity_time_interval,
          bill_payer_account_id,
          line_item_usage_account_id,
          line_item_line_item_type,
          line_item_product_code,
          line_item_resource_id,
          line_item_usage_start_date,
          line_item_usage_end_date,
          line_item_usage_type,
          line_item_operation,
          line_item_usage_amount,
          line_item_normalization_factor,
          line_item_normalized_usage_amount,
          line_item_currency_code,
          line_item_unblended_rate,
          line_item_unblended_cost,
          line_item_blended_rate,
          line_item_blended_cost,
          pricing_unit,
          product_servicecode,
          product_instance_type
        FROM COST_AND_USAGE_REPORT
      SQL

      table_configurations = {
        COST_AND_USAGE_REPORT = {
          BILLING_VIEW_ARN                      = "arn:${data.aws_partition.current.partition}:billing::${data.aws_caller_identity.current.account_id}:billingview/primary"
          TIME_GRANULARITY                      = "HOURLY"
          INCLUDE_RESOURCES                     = "TRUE"
          INCLUDE_MANUAL_DISCOUNT_COMPATIBILITY = "FALSE"
          INCLUDE_SPLIT_COST_ALLOCATION_DATA    = "FALSE"
        }
      }
    }

    destination_configurations {
      s3_destination {
        s3_bucket = aws_s3_bucket.cost_data_lake.bucket
        s3_prefix = "raw/aws-cur"
        s3_region = var.aws_region

        s3_output_configurations {
          overwrite   = "CREATE_NEW_REPORT"
          format      = "PARQUET"
          compression = "PARQUET"
          output_type = "CUSTOM"
        }
      }
    }

    refresh_cadence {
      frequency = "SYNCHRONOUS"
    }
  }

  tags = {
    DataSource = "AWS-CUR-2.0"
    DataType   = "Real-AWS-Cost-Usage"
  }

  depends_on = [
    aws_s3_bucket_policy.data_exports
  ]
}