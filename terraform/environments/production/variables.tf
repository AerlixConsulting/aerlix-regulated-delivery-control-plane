variable "project_name"      { type = string; default = "aerlix" }
variable "environment"       { type = string; default = "production" }
variable "aws_region"        { type = string; default = "us-east-1" }
variable "vpc_cidr"          { type = string; default = "10.0.0.0/16" }
variable "db_instance_class" { type = string; default = "db.t3.medium" }
variable "db_name"           { type = string; default = "aerlix_control_plane" }
variable "db_username" {
  type      = string
  sensitive = true
  # No default for production — must be explicitly provided via tfvars or CI secrets.
}
variable "api_image"         { type = string }
variable "api_desired_count" { type = number; default = 2 }
