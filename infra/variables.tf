variable "region" {
  description = "Región de AWS (el proyecto está restringido a una sola)"
  type        = string
  default     = "us-east-2"
}

variable "instance_type" {
  description = "Tipo de instancia (ARM/Graviton)"
  type        = string
  default     = "t4g.micro"
}

variable "github_repo" {
  description = "Repo autorizado a desplegar vía OIDC (owner/repo, respetando mayúsculas)"
  type        = string
  default     = "martincitouU/liked-in"
}

variable "notes_repo" {
  description = "Repo donde el bot guarda las notas"
  type        = string
  default     = "martincitouU/aprendizaje"
}

variable "llm_model" {
  description = "Modelo de Claude para los resúmenes"
  type        = string
  default     = "claude-haiku-5-5"
}
