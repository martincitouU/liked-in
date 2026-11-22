# GitHub Actions entra a AWS con OIDC: tokens temporales, sin access keys guardadas.

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "deploy" {
  name = "liked-in-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          # GitHub incluye los IDs inmutables del dueño y del repo (owner@id/repo@id)
          "token.actions.githubusercontent.com:sub" = "repo:martincitouU@166942942/liked-in@1467210070:environment:production"
        }
      }
    }]
  })
}

# Lo único que puede hacer el deploy: mandar comandos a ESTA instancia y leer el resultado
resource "aws_iam_role_policy" "deploy" {
  name = "desplegar-en-la-instancia"
  role = aws_iam_role.deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "ssm:SendCommand"
        Resource = [
          aws_instance.bot.arn,
          "arn:aws:ssm:${var.region}::document/AWS-RunShellScript",
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"]
        Resource = "*"
      },
    ]
  })
}
