# ts_homogeneous_cluster_ssm
Terraform resources for provisioning and configuring TS homogeneous cluster through AWS SSM.

## Getting Started
These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes.

This repo contains terraform tf code that is designed to provision a multi node
ThoughtSpot Cluster and install it through SSM.

The process covers below two fold steps
  - Prepare your base AMI to install ThoughtSpot Cluster
  - Install the ThoughtSpot Cluster

### Prerequisites

Before using this resources, you will need to have these artefacts ready with you.

* AWS:
  - Amazon Linux 2 base AMI
  - VPC ID
  - SUBNET ID
  - SECURITY GROUPS (with all necessary access for accessing the app from your network)
  - Instance profile that provide below described permissions
      * This must provide permissions to access SSM, EC2, S3 bucket etc.
      https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-profile.html


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
$ cd community-tools/ThoughtSpot_Cloud_deployments/community-tools/ThoughtSpot_Cloud_deployments/AWS/template_Homogeneous_cluster_ssm/without_role_creation/ts_cluster_ssm/

```
:point_right:Please do not move any of the files around in this directory

#### Provide inputs for the provisioning and installation
:point_right: Only terraform.tfvars.tf file need to be modified.
No other file should require any change for this to work.

Update the variable file terraform.tfvars.tf with details as described.
Some of them already has some default values which can be used as such.
```
mv terraform.tfvars.template terraform.tfvars
vim terraform.tfvars.tf
```
* Cluster specific variables (example values below):
  - customer_name           = "customer"
  - cluster_id              = "ABCX9999000"
  - cluster_name            = "custALCluster03"
  - alert_email             = "alertingprod@myalertemail.com"
  - release                 = "6.1.1-2"
  - subnet_id               = "subnet-74269272342e"
  - vpc_id                  = "vpc-81b6284643235f8"
  - ami                     = "ami-0d66216454c01e8c2de2c"
  - vpc_security_group_ids  = ["sg-886dfw98ecf7","sg-ec86jd654f293"]
  - no_of_instance          = 10
  - instance_profile        = "instanceprofilename"
  - instance_type           = "r4.16xlarge"
  - root_vol_size           = "100"
  - export_vol_size         = "200"
  - data_vol_size           = "1024"
  - ssm_document_name       = "SSM-SessionManagerRunShell-customer09"
  - s3_bucket_name          = "bucket-name"
  - user_data               = "./scripts/user_data.sh"

#### Modify the associated shell scripts
There are a couple of shell scripts which would be used to bootstrap the instance
preparation and installation process.

- ./scripts/prepare_host_ts.sh
- ./scripts/install_ts.sh

Modify these sed replace strings matching the required information specific to your environment
```
cd scripts/
sed -i 's/<OFFLINE_ANSIBLE_TARBALL_FILE>/6.1.1-2.offline.ansible.tar.gz/g' prepare_host_ts.sh
sed -i 's/<S3_BUCKET_WITH_FOLDER_IF_ANY>/bucket-name/g' prepare_host_ts.sh

sed -i 's/<TS_RELEASE_TARBALL>/6.1.1-2.tar.gz/g' install_ts.sh
sed -i 's/<RELEASE>/6.1.1-2/g' install_ts.sh
sed -i 's/<S3_BUCKET>/bucket-name/g' install_ts.sh
sed -i 's/<S3_BUCKET_WITH_FOLDER>/bucket-name/g' install_ts.sh
```

:point_right:Please note these files will be automatically uploaded to your S3 bucket by terraform
The S3 bucket should have proper permissions enabled for this.

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
:point_right: **This will trigger two SSM commands**
1. **first prepare provisioned instances with offline ansible tar**
2. **Then the installation is kick-started which can be monitored from SSM**

### State file management
Terraform creates a file called terraform.tfstate which describes the provisioned infrastructure.
This file needs to be managed properly.
There are a number of ways to do it, This repo implements local state file.
https://www.terraform.io/docs/state/index.html
https://blog.gruntwork.io/how-to-manage-terraform-state-28f5697e68fa

## Troubleshooting

* A lot of issues usually occur because of incorrect or insufficient permissions
- check the IAM roles and policies
- terraform needs full access for EC2, S3 and SSM

* S3 access should be properly checked as terraform and SSM access S3 to move files around
- validate S3 permissions
- make sure proper encryption key is used
