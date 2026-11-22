output "instance_id" {
  description = "ID de la instancia (para el deploy vía SSM)"
  value       = aws_instance.bot.id
}

output "deploy_role_arn" {
  description = "Rol que asume GitHub Actions vía OIDC"
  value       = aws_iam_role.deploy.arn
}

output "region" {
  value = var.region
}
