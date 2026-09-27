variable "aws_region" {
  description = "AWS region for the project"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cloud-cost-optimization"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "data_export_name" {
  description = "AWS Cost and Usage Data Export name"
  type        = string
  default     = "cloud-cost-optimization-cur"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for controlled workload experiments"
  type        = string
  default     = "t3.micro"
}

variable "rds_instance_class" {
  description = "RDS instance class for controlled database workload experiments"
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "17"
}

variable "rds_database_name" {
  description = "Application database name"
  type        = string
  default     = "costanalytics"
}

variable "rds_master_username" {
  description = "RDS master username"
  type        = string
  default     = "costadmin"
}