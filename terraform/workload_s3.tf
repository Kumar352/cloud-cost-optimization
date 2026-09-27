# ============================================================
# WORKLOAD S3 BUCKET
# Separate from the primary analytics data lake.
# ============================================================

resource "aws_s3_bucket" "workload" {
  bucket = "${var.project_name}-workload-${data.aws_caller_identity.current.account_id}"

  force_destroy = true

  tags = {
    Name      = "${var.project_name}-workload"
    Component = "Workload"
    Service   = "S3"
    Workload  = "Controlled-S3-Experiment"
  }
}

resource "aws_s3_bucket_versioning" "workload" {
  bucket = aws_s3_bucket.workload.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "workload" {
  bucket = aws_s3_bucket.workload.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "workload" {
  bucket = aws_s3_bucket.workload.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "workload" {
  bucket = aws_s3_bucket.workload.id

  rule {
    id     = "workload-retention"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 3
    }
  }
}

output "workload_s3_bucket" {
  description = "S3 bucket used by controlled workload experiments"
  value       = aws_s3_bucket.workload.bucket
}