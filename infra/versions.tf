terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # El estado vive en el bucket creado por infra/bootstrap
  backend "s3" {
    bucket       = "liked-in-tfstate-166952590856"
    key          = "liked-in/terraform.tfstate"
    region       = "us-east-2"
    encrypt      = true
    use_lockfile = true # bloqueo nativo en S3: evita dos apply simultáneos
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "liked-in"
      ManagedBy = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
