# Aerlix Regulated Delivery Control Plane — Terraform Root Configuration
#
# This file declares backend, provider, and root-level variable defaults.
# Environment-specific configurations live under environments/{staging,production}.
#
# Usage:
#   cd terraform/environments/staging
#   terraform init
#   terraform plan -var-file=terraform.tfvars
#   terraform apply -var-file=terraform.tfvars

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "aerlix-control-plane"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "aerlix-engineering"
    }
  }
}
