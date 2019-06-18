################################################################################
# IMPORTANT: Make sure to set the aws credentials as an environment variable
# before starting this.
#   export AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#   export AWS_ACCESS_KEY_ID=yyyyyyyyyyyyyyyyy
################################################################################

# MODIFY THIS ACCORDING TO EACH DEPLOYMENT
################################################################################
# Cluster details
################################################################################
variable "customer_name" {
  description = "The instance name to be created (prefixed). Also the cluster name"
  default     = "testBlogCluster"
}
variable "number_of_instances" {
  description = "The number of nodes in cluster"
  default = "2"
}
variable "release" {
  description = "The Release version to be installed"
  default = "5.2.CU1"
}
variable "inst_size" {
  description = "The size of the ec2 resource to provision mapped later"
  default = "lean"
}
variable "cluster_id" {
  description = "The cluster_id for this installation"
  default = "12345678"
}
variable "alert_email" {
  description = "The alert email to be configured on cluster"
  default = "later"
}
variable "release_location" {
  description = "The directory where the Release tar file is located"
  default = "../.."
}
################################################################################
# AWS account related information
################################################################################
variable "region" {
  description = "The AWS region."
  default = ""
}
variable "ami_id" {
  default = ""
}
variable "ts_instance_type" {
  description = "The instance type to launch "
  default     = {
    "lean"        = "r4.4xlarge"
    "standard"    = "r4.16xlarge"
    }
}
variable "vpc_subnet_id" {
  description = "The Subnet associated this instance"
  default     = ""
}
variable "security_groups" {
  type        = "list"
  description = "The Security groups associated with the instance"
  default     = [""]
}
# variable "vol_size" {
#   description = "The size of data disks to provision"
#   default = 1000
# }
variable "key_name" {
  # Doesn't work now on current TS AMI
  description = "The AWS key pair to be attached with ec2."
  default = ""
}
################################################################################
# Ansible Specific inputs
################################################################################
variable "playbook" {
  description = "The ansible playbook to configure the instance"
  default = "ts-provision.yaml"
}
variable "ssh_user" {
  description = "The default user account used for configuring the system"
  default     = "admin"
}
variable "admin_password" {
  description = "The admin user password. Asked interactively during plan/apply"
}
