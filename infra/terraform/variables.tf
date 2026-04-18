variable "aws_region" {
  description = "AWS region"
  type        = "string"
  default     = "us-east-1"
}

variable "db_password" {
  description = "Password for the RDS PostgreSQL instance"
  type        = "string"
  sensitive   = true
}
