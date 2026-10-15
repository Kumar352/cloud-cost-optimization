# Optional CUR catalog/query layer.
#
# These resources are declared in Terraform but are not deployed automatically by
# adding this file. Review terraform plan before applying. Running a Glue crawler
# or Athena queries can incur charges; the crawler intentionally has no schedule.

resource "aws_glue_catalog_database" "cur" {
  name        = "${replace(var.project_name, "-", "_")}_cur"
  description = "AWS CUR 2.0 Data Catalog for Cloud Cost Optimization Analytics"
}

resource "aws_glue_crawler" "cur" {
  name          = "${var.project_name}-cur-crawler"
  description   = "Catalog AWS CUR 2.0 Parquet partitions in the project data lake"
  role          = aws_iam_role.glue_service.arn
  database_name = aws_glue_catalog_database.cur.name

  s3_target {
    path = "s3://${aws_s3_bucket.cost_data_lake.bucket}/raw/aws-cur/cloud-cost-optimization-cur/data/"
  }

  recrawl_policy {
    recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  tags = {
    Component  = "DataCatalog"
    DataSource = "AWS-CUR-2.0"
  }

  depends_on = [
    aws_iam_role_policy.glue_data_lake_access
  ]
}

resource "aws_s3_object" "athena_results_prefix" {
  bucket  = aws_s3_bucket.cost_data_lake.id
  key     = "reports/athena-results/"
  content = ""
}

resource "aws_athena_workgroup" "cur_analytics" {
  name          = "${var.project_name}-cur-analytics"
  description   = "Cost-controlled Athena workgroup for AWS CUR 2.0 analysis"
  state         = "ENABLED"
  force_destroy = false

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query    = 52428800

    result_configuration {
      output_location = "s3://${aws_s3_bucket.cost_data_lake.bucket}/reports/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }

  tags = {
    Component  = "Analytics"
    DataSource = "AWS-CUR-2.0"
  }

  depends_on = [
    aws_s3_object.athena_results_prefix,
    aws_glue_catalog_database.cur,
  ]
}

output "cur_glue_database_name" {
  description = "Glue Catalog database for AWS CUR 2.0"
  value       = aws_glue_catalog_database.cur.name
}

output "cur_glue_crawler_name" {
  description = "Manually triggered crawler for AWS CUR 2.0"
  value       = aws_glue_crawler.cur.name
}

output "cur_athena_workgroup_name" {
  description = "Athena workgroup with query result encryption and a 50 MiB scan cutoff"
  value       = aws_athena_workgroup.cur_analytics.name
}
