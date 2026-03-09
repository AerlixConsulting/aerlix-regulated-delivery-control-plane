output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "api_url" {
  description = "Public URL of the API load balancer"
  value       = module.compute.api_alb_dns_name
}

output "db_endpoint" {
  description = "PostgreSQL RDS endpoint (host:port)"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.compute.ecs_cluster_name
}
