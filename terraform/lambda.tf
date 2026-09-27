data "archive_file" "workload_lambda" {
  type        = "zip"
  source_file = "${path.module}/lambda/workload.py"
  output_path = "${path.module}/lambda/workload.zip"
}

resource "aws_lambda_function" "workload" {
  function_name = "${var.project_name}-workload-generator"
  description   = "Controlled workload generator for cloud cost experiments"

  role = aws_iam_role.lambda_execution.arn

  handler = "workload.lambda_handler"
  runtime = "python3.14"

  filename         = data.archive_file.workload_lambda.output_path
  source_code_hash = data.archive_file.workload_lambda.output_base64sha256

  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      WORKLOAD_BUCKET = aws_s3_bucket.workload.bucket
      PROJECT_NAME    = var.project_name
    }
  }

  tags = {
    Name       = "${var.project_name}-lambda-workload"
    Workload   = "Controlled-Cost-Experiment"
    DataSource = "AWS"
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda
  ]
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-workload-generator"
  retention_in_days = 14

  tags = {
    Name    = "${var.project_name}-lambda-logs"
    Purpose = "Workload experiment logging"
  }
}

resource "aws_cloudwatch_event_rule" "workload" {
  name        = "${var.project_name}-workload-schedule"
  description = "Low-frequency scheduled Lambda workload for controlled cost experiments"

  schedule_expression = "rate(1 hour)"

  tags = {
    Name    = "${var.project_name}-workload-schedule"
    Purpose = "Controlled workload experiment"
  }
}

resource "aws_cloudwatch_event_target" "workload" {
  rule = aws_cloudwatch_event_rule.workload.name
  arn  = aws_lambda_function.workload.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.workload.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.workload.arn
}

output "lambda_function_name" {
  description = "Lambda workload function name"
  value       = aws_lambda_function.workload.function_name
}

output "lambda_function_arn" {
  description = "Lambda workload function ARN"
  value       = aws_lambda_function.workload.arn
}

output "lambda_log_group" {
  description = "Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "eventbridge_rule_name" {
  description = "EventBridge workload schedule"
  value       = aws_cloudwatch_event_rule.workload.name
}