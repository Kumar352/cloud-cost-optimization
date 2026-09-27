# ============================================================
# RDS WORKLOAD DATABASE
# Cloud Cost Optimization Analytics Using Hadoop
# ============================================================

# ------------------------------------------------------------
# Random database password
# ------------------------------------------------------------

resource "random_password" "rds_master" {
  length  = 24
  special = true
}

# ------------------------------------------------------------
# Secrets Manager
# Stores the RDS credentials securely.
# ------------------------------------------------------------

resource "aws_secretsmanager_secret" "rds_credentials" {
  name        = "${var.project_name}/rds/credentials"
  description = "Credentials for the Cloud Cost Optimization PostgreSQL workload database"

  recovery_window_in_days = 0

  tags = {
    Name      = "${var.project_name}-rds-credentials"
    Component = "RDS"
    Purpose   = "Controlled workload experiments"
  }
}

resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id = aws_secretsmanager_secret.rds_credentials.id

  secret_string = jsonencode({
    username = var.rds_master_username
    password = random_password.rds_master.result
    database = var.rds_database_name
    engine   = "postgres"
    port     = 5432
  })
}

# ------------------------------------------------------------
# Private DB subnet group
# ------------------------------------------------------------

resource "aws_db_subnet_group" "workload" {
  name = "${var.project_name}-rds-subnet-group"

  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  tags = {
    Name      = "${var.project_name}-rds-subnet-group"
    Component = "RDS"
    Tier      = "Private"
  }
}

# ------------------------------------------------------------
# PostgreSQL RDS instance
# ------------------------------------------------------------

resource "aws_db_instance" "workload" {
  identifier = "${var.project_name}-postgres"

  engine         = "postgres"
  engine_version = var.rds_engine_version

  instance_class = var.rds_instance_class

  allocated_storage     = 20
  max_allocated_storage = 40
  storage_type          = "gp3"

  storage_encrypted = true

  db_name  = var.rds_database_name
  username = var.rds_master_username
  password = random_password.rds_master.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.workload.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false

  multi_az = false

  backup_retention_period = 3

  backup_window      = "03:00-04:00"
  maintenance_window = "sun:04:00-sun:05:00"

  auto_minor_version_upgrade = true

  deletion_protection = false
  skip_final_snapshot = true

  copy_tags_to_snapshot = true

  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade"
  ]

  performance_insights_enabled = false

  tags = {
    Name       = "${var.project_name}-postgres"
    Component  = "RDS"
    Workload   = "Controlled-Cost-Experiment"
    DataSource = "AWS"
    Purpose    = "Database workload and cost analysis"
  }

  depends_on = [
    aws_db_subnet_group.workload,
    aws_iam_role_policy.ec2_rds_secret_access
  ]
}

# ------------------------------------------------------------
# Outputs
# ------------------------------------------------------------

output "rds_instance_id" {
  description = "RDS PostgreSQL instance identifier"
  value       = aws_db_instance.workload.identifier
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.workload.address
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.workload.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.workload.db_name
}

output "rds_secret_arn" {
  description = "Secrets Manager ARN containing RDS credentials"
  value       = aws_secretsmanager_secret.rds_credentials.arn
}