output "aws_account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "cost_data_lake_bucket" {
  description = "S3 data lake bucket"
  value       = aws_s3_bucket.cost_data_lake.bucket
}

output "cost_data_lake_arn" {
  description = "S3 data lake ARN"
  value       = aws_s3_bucket.cost_data_lake.arn
}

output "cost_usage_export_arn" {
  description = "AWS Cost and Usage Data Export ARN"
  value       = aws_bcmdataexports_export.cost_usage.export[0].export_arn
}