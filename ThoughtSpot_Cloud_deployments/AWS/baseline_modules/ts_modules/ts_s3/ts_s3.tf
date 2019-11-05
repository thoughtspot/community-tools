resource "aws_s3_bucket" "ts-s3" {
  count             = "${var.pre_existing == "" ? 1 : 0}"
  bucket            = "${lower(var.cluster_name)}-${lower(var.cluster_id)}-s3"

  versioning {
    enabled         = true
  }

  lifecycle {
    prevent_destroy = false
  }

  force_destroy = true ##### Remove this before moving to prod

  tags = {
    Name            = "S3 for ${var.cluster_id}"
  }
}

output "s3_bucket_name" {
    description       = "The name of the s3 bucket created"
    value             = "${var.pre_existing != "" ? var.pre_existing : aws_s3_bucket.ts-s3[0].id}"
}
