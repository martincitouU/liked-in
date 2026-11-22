# Configuración NO secreta del bot. Los secretos (tokens y API keys) se crean a mano
# con la CLI para que nunca queden en el estado de Terraform.

locals {
  config = {
    STORAGE     = "github"
    GITHUB_REPO = var.notes_repo
    LLM_MODEL   = var.llm_model
  }
}

resource "aws_ssm_parameter" "config" {
  for_each = local.config

  name  = "/liked-in/${each.key}"
  type  = "String"
  value = each.value
}
