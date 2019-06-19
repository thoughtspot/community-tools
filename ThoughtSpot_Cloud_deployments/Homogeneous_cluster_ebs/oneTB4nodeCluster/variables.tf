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
  default     = "sample4nodeCluster"
}
variable "cluster_id" {
  # Get this from Thoughtspot Support
  description = "The cluster_id for this installation"
  default = ""
}
variable "inst_size" {
  description = "The size of the ec2 resource to provision mapped later"
  default = "lean"
}
variable "number_of_instances" {
  description = "The number of nodes in cluster"
  default = "4"
}
variable "release" {
  # Get this from Thoughtspot Support
  description = "The Release version to be installed."
  default = ""
}
variable "release_location" {
  # Specify the location where release tar and MD5checksum files are kept
  description = "The directory where the Release tar file is located"
  default = "/home/ec2-user"
}
variable "alert_email" {
  description = "The alert email to be configured on cluster"
  default = "later"
}
################################################################################
# AWS account related information
################################################################################
variable "region" {
  description = "The AWS region where this resources will be created."
  default = ""
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
  # Get this from Thoughtspot Support
  description = "The admin user password. Asked interactively during plan/apply"
}
