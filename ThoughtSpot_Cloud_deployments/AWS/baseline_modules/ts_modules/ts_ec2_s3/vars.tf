variable "vpc_subnet_id" {
  description = "VPC subnet id to which we attach these resources to"
}
variable "key_name" {
  description = "The AWS key pair to use for resources."
}
variable "vol_size" {
  description = "The size of disks to provision"
}
variable "cluster_name" {
  description = "The instance name to be created"
}
variable "base_ami" {
  description = "The base ami used to launch instance"
}
variable "ts_instance_type" {
  description = "The instance type to launch "
}
variable "number_of_instances" {
  description = "The number of instances to launch "
}
variable "security_groups" {
  type        = "list"
  description = "The security groups that needs to be attached to instance"
}
variable "iam_instance_profile" {
  description = "The instance profile attached to ec2"
}
