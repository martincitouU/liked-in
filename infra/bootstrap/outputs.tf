output "state_bucket" {
  description = "Bucket para el backend S3 de infra/"
  value       = aws_s3_bucket.tfstate.bucket
}
