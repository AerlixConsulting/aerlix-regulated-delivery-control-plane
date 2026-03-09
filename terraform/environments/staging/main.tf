# Staging environment entry point
# Uses the root terraform modules

terraform {
  required_version = ">= 1.7.0"

  # Uncomment and configure for remote state:
  # backend "s3" {
  #   bucket         = "aerlix-terraform-state"
  #   key            = "staging/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "aerlix-terraform-locks"
  #   encrypt        = true
  # }
}

module "networking" {
  source = "../../modules/networking"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

module "database" {
  source = "../../modules/database"

  project_name          = var.project_name
  environment           = var.environment
  private_subnet_ids    = module.networking.private_subnets
  vpc_id                = module.networking.vpc_id
  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  api_security_group_id = module.compute.api_security_group_id
}

module "compute" {
  source = "../../modules/compute"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnets
  private_subnet_ids = module.networking.private_subnets
  api_image          = var.api_image
  api_desired_count  = var.api_desired_count
  db_endpoint        = module.database.db_endpoint
  db_username        = var.db_username
  db_password        = module.database.db_password
  db_name            = var.db_name
}
