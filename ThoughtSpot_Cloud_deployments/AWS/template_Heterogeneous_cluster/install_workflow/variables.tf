# MODIFY ACCORDING TO EACH DEPLOYMENT
variable "cluster_name" {
  description = "The instance name to be created (prefixed)."
  default     = "clusterName"
}
variable "cluster_id" {
  # Provided by TS Support
  description = "The cluster_id for this installation"
  default     = "id"
}
variable "release" {
  description = "The Release version to be installed"
  default     = "5.3"
}
variable "release_directory" {
  # This file is located on the deployment host at a location accessible by
  # the user invoking this script
  description = "The directory where the Release tar file is located"
  default     = "/release_tars"
}
variable "alert_email" {
  description = "The alert email to be configured on cluster"
  default     = "later"
}
variable "number_of_falcon" {
  description = "The number of instance needed for falcon"
  default = "n"
}
variable "number_of_metadata_nodes" {
  description = "The number of instance needed for callosum and sage"
  default = "n"
}
################################################################################
# THESE MOSTLY REMAIN CONSTANT PER ENVIRONMENT
################################################################################
variable "region" {
  description = "The AWS region."
  default = "region-of-your-deployment"
}
variable "base_ami" {
  description = "The ami used to launch the instances"
  default = "ami-you-got-from-support-or-docs"
}
variable "vol_size" {
  description = "The size of data volumes for each instances. Created in pairs"
  default     = 1024
}
variable "vpc_subnet_id" {
  description = "The Subnet associated this instance"
  default     = "subnet-your-vpc-subnet-id"
}
variable "security_groups" {
  type        = "list"
  description = "The Security groups associated with the instance"
  default     = ["sg-your-sgs"]
}
variable "owner_tag" {
  description = "The tag to represent ownership of the instances"
  default = "Who-owns-these-vms"
}
################################################################################
# HETEROGENEOUS INFRA SETUP
################################################################################
variable "ts_instance_type" {
  description = "The instance type to launch for each components"
  default     = {
    "falcon"        = "r5.16xlarge"
    "metadata"      = "r5.8xlarge"
    }
}
variable "scheduling_policy" {
  # either LABEL_ALL_HOSTS or LABEL_SIZE
  description = "The service scheduling policy for the cluster"
  default = "LABEL_ALL_HOSTS"
}
################################################################################
# ANSIBLE SPECIFIC VALUES - DO NOT CHANGE
################################################################################
variable "playbook" {
  description = "The ansible playbook to create a heterogeneous cluster"
  default = "ts-ProvisionHetrogeneous.yaml"
}

variable "ssh_user" {
  description = "The default user account used for configuring the system"
  default     = "admin"
}
