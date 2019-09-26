variable "cluster_name" {
  description = "The cluster name prefixed for the S3 bucket name"
}
variable "cluster_id" {
  description = "The cluster id prefixed for the S3 bucket name"
}
variable "pre_existing" {
  description = "Do not create an S3 bucket if this value is set"
}
