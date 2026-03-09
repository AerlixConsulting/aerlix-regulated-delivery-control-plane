# Global input variables shared across all environments.

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name (staging | production)"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be 'staging' or 'production'."
  }
}

variable "project_name" {
  description = "Short project identifier used in resource names"
  type        = string
  default     = "aerlix"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_instance_class" {
  description = "RDS instance class for the PostgreSQL database"
  type        = string
  default     = "db.t3.medium"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "aerlix_control_plane"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "aerlix"
  sensitive   = true
}

variable "api_image" {
  description = "Container image URI for the API service"
  type        = string
}

variable "frontend_image" {
  description = "Container image URI for the frontend service"
  type        = string
}

variable "api_desired_count" {
  description = "Desired number of API ECS task instances"
  type        = number
  default     = 2
}
