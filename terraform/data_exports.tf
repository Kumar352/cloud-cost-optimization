resource "aws_s3_bucket_policy" "data_exports" {
  bucket = aws_s3_bucket.cost_data_lake.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "EnableAWSDataExportsToWriteToS3"
        Effect = "Allow"

        Principal = {
          Service = [
            "bcm-data-exports.amazonaws.com"
          ]
        }

        Action = [
          "s3:PutObject"
        ]

        Resource = "${aws_s3_bucket.cost_data_lake.arn}/*"

        Condition = {
          ArnLike = {
            "aws:SourceArn" = "arn:${data.aws_partition.current.partition}:bcm-data-exports:${var.aws_region}:${data.aws_caller_identity.current.account_id}:export/*"
          }

          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  depends_on = [
    aws_s3_bucket_public_access_block.cost_data_lake
  ]
}