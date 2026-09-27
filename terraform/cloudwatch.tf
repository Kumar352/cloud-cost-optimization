# ============================================================
# CLOUDWATCH OBSERVABILITY
# ============================================================

resource "aws_cloudwatch_metric_alarm" "ec2_cpu_high" {
  alarm_name          = "${var.project_name}-ec2-high-cpu"
  alarm_description   = "Detect elevated EC2 CPU utilization during cost experiments"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300

  metric_name = "CPUUtilization"
  namespace   = "AWS/EC2"
  statistic   = "Average"

  threshold = 70

  dimensions = {
    InstanceId = aws_instance.workload.id
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name      = "${var.project_name}-ec2-high-cpu"
    Component = "Observability"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${var.project_name}-rds-high-cpu"
  alarm_description   = "Detect elevated RDS CPU utilization during database experiments"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300

  metric_name = "CPUUtilization"
  namespace   = "AWS/RDS"
  statistic   = "Average"

  threshold = 70

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.workload.id
  }

  treat_missing_data = "notBreaching"

  tags = {
    Name      = "${var.project_name}-rds-high-cpu"
    Component = "Observability"
  }
}

resource "aws_cloudwatch_dashboard" "workloads" {
  dashboard_name = "${var.project_name}-workloads"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          title = "EC2 CPU Utilization"

          metrics = [
            [
              "AWS/EC2",
              "CPUUtilization",
              "InstanceId",
              aws_instance.workload.id
            ]
          ]

          period = 300
          stat   = "Average"
          region = var.aws_region
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          title = "RDS CPU Utilization"

          metrics = [
            [
              "AWS/RDS",
              "CPUUtilization",
              "DBInstanceIdentifier",
              aws_db_instance.workload.id
            ]
          ]

          period = 300
          stat   = "Average"
          region = var.aws_region
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          title = "Lambda Invocations"

          metrics = [
            [
              "AWS/Lambda",
              "Invocations",
              "FunctionName",
              aws_lambda_function.workload.function_name
            ]
          ]

          period = 300
          stat   = "Sum"
          region = var.aws_region
          view   = "timeSeries"
        }
      }
    ]
  })
}