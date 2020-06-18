# ts_homogeneous_cluster_restore_ssm
Terraform resources for Refreshing AMI and restoring TS homogeneous cluster through AWS SSM.

## Getting Started
These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes.

This repo contains terraform tf code that is designed to provision a multi node
ThoughtSpot Cluster and install it through SSM.

The process covers below two fold steps
  - Prepare your base AMI to install ThoughtSpot Cluster
  - Restore the ThoughtSpot Cluster from a backup in EFS mounted volume

### Prerequisites

Before using this resources, you will need to have these artefacts ready with you.

* Infrastructure components:
  - Amazon Linux 2 base AMI
  - VPC ID
  - SUBNET ID
  - SECURITY GROUPS (with all necessary access for accessing the app from your network)

* Your aws environment specific details
  * For access:
    - AWS_SECRET_ACCESS_KEY
    - AWS_ACCESS_KEY_ID
    add the above variables in your environment

* Obtain below files and details from ThoughtSpot Support:

:point_right:Please create a new bucket in S3 and upload the below files (place within the root folder to minimise editing the terraform scripts)
  - [release_version].offline.ansible.tar.gz
  - [release_version].tar.gz

:point_right:Copy the above two files into your S3 bucket and note down the path.

  - The cluster ID  
  - The cluster name  
  - Email to receive alert

* These details would be needed to provide as input for terraform in the coming sections

:warning: **Please do not proceed without the above details in hand**

### Setup the deployment server

Setup an environment where you have terraform version 0.12.24 installed.
set up environment
```
export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AWS_ACCESS_KEY_ID="yyyyyyyyyyyyyyyyy"
```
  - Would require internet access from this host to get provider binaries for terraform

### Provisioning infra and installing ThoughtSpot
#### Get the code repository
Clone this repo
```
$ git clone https://github.com/thoughtspot/community-tools.git
$ cd community-tools/ThoughtSpot_Cloud_deployments/template_Homogeneous_cluster_ssm/
```
:point_right:Please do not move any of the files around in this directory

#### Provide inputs for the provisioning and installation
:point_right: Only terraform.tfvars.tf file need to be modified.
No other file should require any change for this to work.

Update the variable file terraform.tfvars.tf with details as described.
Some of them already has some default values which can be used as such.
```
vim terraform.tfvars.tf
```
* Cluster specific variables (example values below):
      - customer_name           = "appRestore1"
      - cluster_id              = "999X888199"
      - cluster_name            = "custALCluster01"
      - alert_email             = "alert@myalertemail.com"
      - release                 = "6.1.1-2"
      - subnet_id               = "subnet-7426922e"
      - vpc_id                  = "vpc-81b625f8"
      - ami                     = "ami-0d6621c01e8c2de2c"
      - vpc_security_group_ids  = ["sg-8898ecf7","sg-ec86f293"]
      - no_of_instance          = 4
      - instance_type           = "r4.16xlarge"
      - root_vol_size           = "100"
      - export_vol_size         = "200"
      - data_vol_size           = "400"
      - ssm_document_name       = "SSM-restore-01"
      - s3_bucket_name          = "aaron-sre"
      - user_data               = "user_data.sh"
      - s3_path_of_tar          = "aaron-sre"
      - offline_ansible_tar     = "6.1.1-2.offline.ansible.tar.gz"
      - mount_target_host       = "192.168.7.183"
      - mount_target_dir        = "/mnt/tstore/Backups"
      - backup_subdir           = "sre_share/app_test/full_backup"


### Initialise terraform
As first step initialise terraform to get necessary binaries and setup backends
You should be in the directory created above.
This should pull in binaries for various providers and make sure you are ready to launch your infra.
```
terraform init
```
### Launch infra
Terraform provides a step to see what it will create before actually creating the physical world.
This step gives a dry-run of what actions terraform will perform to create your infrastructure.
```
terraform plan
```
This step creates the infrastructure as defined in the tf files
```
terraform apply
```
:point_right: **This will trigger two jobs**
1. **first prepare provisioned instances with offline ansible tar**
2. **Then the restoration is kick-started which can be monitored from SSM**

### State file management
Terraform creates a file called terraform.tfstate which describes the provisioned infrastructure.
This file needs to be managed properly.
There are a number of ways to do it, This repo implements local state file.
https://www.terraform.io/docs/state/index.html
https://blog.gruntwork.io/how-to-manage-terraform-state-28f5697e68fa
