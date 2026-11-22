# La instancia del bot y su rol IAM.

# AMI más reciente de Amazon Linux 2023 para ARM, publicada por AWS en SSM
data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

resource "aws_iam_role" "bot" {
  name = "liked-in-bot-instance"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Permite administrar la instancia con SSM (comandos y sesiones) sin SSH
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.bot.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Solo puede leer SUS parámetros (/liked-in/*), nada más de la cuenta
resource "aws_iam_role_policy" "read_params" {
  name = "leer-parametros-liked-in"
  role = aws_iam_role.bot.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParametersByPath", "ssm:GetParameters", "ssm:GetParameter"]
      Resource = [
        "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/liked-in",
        "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/liked-in/*",
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "bot" {
  name = "liked-in-bot"
  role = aws_iam_role.bot.name
}

resource "aws_instance" "bot" {
  ami                    = data.aws_ssm_parameter.al2023_arm64.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.bot.id]
  iam_instance_profile   = aws_iam_instance_profile.bot.name

  user_data                   = file("${path.module}/user_data.sh")
  user_data_replace_on_change = true

  metadata_options {
    http_tokens = "required" # IMDSv2 obligatorio
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  tags = { Name = "liked-in-bot" }

  lifecycle {
    # Una AMI nueva no debe recrear la instancia en cada plan; se parcha con dnf
    ignore_changes = [ami]
  }
}
