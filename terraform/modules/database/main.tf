# Database module — RDS PostgreSQL (Multi-AZ in production)

variable "project_name"      { type = string }
variable "environment"       { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "vpc_id"            { type = string }
variable "db_instance_class" { type = string }
variable "db_name"           { type = string }
variable "db_username"       { type = string; sensitive = true }
variable "api_security_group_id" { type = string }

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.private_subnet_ids
  tags = { Name = "${var.project_name}-${var.environment}-db-subnet" }
}

resource "aws_security_group" "db" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Allow PostgreSQL from API tasks only"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.api_security_group_id]
    description     = "PostgreSQL from API"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "main" {
  identifier              = "${var.project_name}-${var.environment}-postgres"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = var.db_instance_class
  allocated_storage       = 20
  max_allocated_storage   = 100
  storage_encrypted       = true
  db_name                 = var.db_name
  username                = var.db_username
  password                = random_password.db.result
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  multi_az                = var.environment == "production"
  deletion_protection     = var.environment == "production"
  skip_final_snapshot     = var.environment != "production"
  backup_retention_period = var.environment == "production" ? 7 : 1
  tags = { Name = "${var.project_name}-${var.environment}-postgres" }
}

output "db_endpoint" { value = aws_db_instance.main.endpoint; sensitive = true }
output "db_password" { value = random_password.db.result; sensitive = true }
