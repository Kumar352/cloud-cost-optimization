resource "aws_s3_bucket" "cost_data_lake" {
  bucket = "${var.project_name}-${data.aws_caller_identity.current.account_id}"

  force_destroy = false
}

resource "aws_s3_bucket_versioning" "cost_data_lake" {
  bucket = aws_s3_bucket.cost_data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cost_data_lake" {
  bucket = aws_s3_bucket.cost_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "cost_data_lake" {
  bucket = aws_s3_bucket.cost_data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cost_data_lake" {
  bucket = aws_s3_bucket.cost_data_lake.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cost_data_lake" {
  bucket = aws_s3_bucket.cost_data_lake.id

  rule {
    id     = "cost-data-retention"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_object" "raw_prefix" {
  bucket = aws_s3_bucket.cost_data_lake.id
  key    = "raw/"
}

resource "aws_s3_object" "processed_prefix" {
  bucket = aws_s3_bucket.cost_data_lake.id
  key    = "processed/"
}

resource "aws_s3_object" "analytics_prefix" {
  bucket = aws_s3_bucket.cost_data_lake.id
  key    = "analytics/"
}

resource "aws_s3_object" "reports_prefix" {
  bucket = aws_s3_bucket.cost_data_lake.id
  key    = "reports/"
}