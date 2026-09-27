# ============================================================
# IAM ROLES AND POLICIES
# Cloud Cost Optimization Analytics Using Hadoop
# ============================================================


# ------------------------------------------------------------
# EC2 WORKLOAD ROLE
# ------------------------------------------------------------

resource "aws_iam_role" "ec2_workload" {
  name = "${var.project_name}-ec2-workload-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "EC2AssumeRole"
        Effect = "Allow"

        Principal = {
          Service = "ec2.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}


# ------------------------------------------------------------
# EC2 → CLOUDWATCH
# ------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "ec2_cloudwatch_agent" {
  role       = aws_iam_role.ec2_workload.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}


# ------------------------------------------------------------
# EC2 → SYSTEMS MANAGER
# ------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_workload.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}


# ------------------------------------------------------------
# EC2 INSTANCE PROFILE
# ------------------------------------------------------------

resource "aws_iam_instance_profile" "ec2_workload" {
  name = "${var.project_name}-ec2-workload-profile"
  role = aws_iam_role.ec2_workload.name
}


# ------------------------------------------------------------
# EC2 → SECRETS MANAGER
# ------------------------------------------------------------

resource "aws_iam_role_policy" "ec2_rds_secret_access" {
  name = "${var.project_name}-ec2-rds-secret-access"
  role = aws_iam_role.ec2_workload.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "ReadRDSCredentials"
        Effect = "Allow"

        Action = [
          "secretsmanager:GetSecretValue"
        ]

        Resource = aws_secretsmanager_secret.rds_credentials.arn
      }
    ]
  })
}


# ------------------------------------------------------------
# LAMBDA EXECUTION ROLE
# ------------------------------------------------------------

resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "LambdaAssumeRole"
        Effect = "Allow"

        Principal = {
          Service = "lambda.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}


# ------------------------------------------------------------
# LAMBDA → CLOUDWATCH LOGGING
# ------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


# ------------------------------------------------------------
# LAMBDA → WORKLOAD S3
# ------------------------------------------------------------
#
# Least-privilege policy.
#
# Lambda can ONLY write objects under:
#
# analytics/lambda-workloads/*
#
# It cannot:
# - delete objects
# - list the bucket
# - modify bucket configuration
# - write to unrelated prefixes
#
# ------------------------------------------------------------

resource "aws_iam_role_policy" "lambda_workload_s3_access" {
  name = "${var.project_name}-lambda-workload-s3-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "WriteLambdaWorkloadArtifacts"
        Effect = "Allow"

        Action = [
          "s3:PutObject"
        ]

        Resource = "${aws_s3_bucket.workload.arn}/analytics/lambda-workloads/*"
      }
    ]
  })
}


# ------------------------------------------------------------
# GLUE SERVICE ROLE
# ------------------------------------------------------------

resource "aws_iam_role" "glue_service" {
  name = "${var.project_name}-glue-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "GlueAssumeRole"
        Effect = "Allow"

        Principal = {
          Service = "glue.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}


# ------------------------------------------------------------
# GLUE SERVICE MANAGED POLICY
# ------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}


# ------------------------------------------------------------
# GLUE → PROJECT DATA LAKE
# ------------------------------------------------------------
#
# Preserves the original Terraform resource name:
# aws_iam_role_policy.glue_data_lake_access
#
# This prevents Terraform from destroying and recreating
# the existing IAM policy simply because of a resource rename.
# ------------------------------------------------------------

resource "aws_iam_role_policy" "glue_data_lake_access" {
  name = "${var.project_name}-glue-data-lake-access"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "ListProjectBucket"
        Effect = "Allow"

        Action = [
          "s3:ListBucket"
        ]

        Resource = aws_s3_bucket.cost_data_lake.arn

        Condition = {
          StringLike = {
            "s3:prefix" = [
              "raw/*",
              "processed/*",
              "analytics/*",
              "reports/*"
            ]
          }
        }
      },
      {
        Sid    = "ReadWriteProjectData"
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]

        Resource = [
          "${aws_s3_bucket.cost_data_lake.arn}/raw/*",
          "${aws_s3_bucket.cost_data_lake.arn}/processed/*",
          "${aws_s3_bucket.cost_data_lake.arn}/analytics/*",
          "${aws_s3_bucket.cost_data_lake.arn}/reports/*"
        ]
      }
    ]
  })
}


# ------------------------------------------------------------
# OUTPUTS
# ------------------------------------------------------------

output "ec2_workload_role_arn" {
  description = "IAM role ARN used by the EC2 workload instance"
  value       = aws_iam_role.ec2_workload.arn
}

output "ec2_workload_instance_profile" {
  description = "EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_workload.name
}

output "lambda_execution_role_arn" {
  description = "IAM role ARN used by the Lambda workload generator"
  value       = aws_iam_role.lambda_execution.arn
}

output "glue_service_role_arn" {
  description = "IAM role ARN used by AWS Glue"
  value       = aws_iam_role.glue_service.arn
}