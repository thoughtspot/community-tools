# ts_homogeneous_cluster
Terraform resources for provisioning and configuring TS homogeneous cluster

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

This repo contains terraform tf code that is designed to provision a multiple ec2 instances and an ansible yaml file to install ThoughSpot Cluster

### Prerequisites

Before using this resources, you will need to have these artefacts ready with you.

- You will need to know the relevant AMI of the ThoughtSpot image - https://docs.thoughtspot.com/5.2/appliance/aws/launch-an-instance.html#about-the-thoughtspot-ami

Below details can be obtained from ThoughtSpot Support:
- You will need to have access to the ThoughtSpot release binary and the MD5checksum file.
- The cluster ID that you will use for configuring the software.
- The username/password used both by ansible and to login to the provisioned instances.

Your aws environment specific details
For access:
- AWS_SECRET_ACCESS_KEY
- AWS_ACCESS_KEY_ID
Network:
- VPC ID
- Security Group ID
- AMI ID (ThoughtSpot AMI described above)

** Please do not proceed without the above details in hand **

### Setup the deployment server
On a deployment server (centos/rhel) need to have these packages installed.
```
$ sudo yum install git ansible
```

Get a copy of this repository and run the playbook to configure this host
```
$ git clone https://github.com/thoughtspot/community-tools.git
$ cd community-tools/ThoughtSpot_Cloud_deployments/Homogeneous_cluster_ebs/deployment_host
$ ansible-playbook terraform.yaml
$ ansible-playbook ansible.yaml
```

This would install terraform and configured ansible as expected.

### Provisioning infra and installing ThoughtSpot
#### Setting up aws specific environment
You need to setup the aws keys as an environment variable for terraform to be able to access your account.

```
export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AWS_ACCESS_KEY_ID="yyyyyyyyyyyyyyyyy"
```

#### Get the code
Clone this repo (same used during deployment host setup)
```
$ git clone https://github.com/thoughtspot/community-tools.git
$ cd community-tools/ThoughtSpot_Cloud_deployments/Homogeneous_cluster_ebs/oneTB4nodeCluster
```
:point_right:Please do not move any of the files around in this directory

#### Provide inputs for the provisioning and installation
:point_right:Only variables.tf file need to be modified. No other file should require any change for this to work.

Update the variable file variables.tf with details as described. Some of them already has some default values which can be used as such.
```
vim vars.tf
```
Cluster specific variables:
  - variable "customer_name" - The name of the cluster, no spaces allowed (eg CompanyFinanceProd)
  - variable "cluster_id" - A unique sting identifier for cluster provided by ThoughtSpot Support team
  - variable "number_of_instances" - The number of nodes in the cluster
  - variable "inst_size" - Only two options [lean or standard]
  - variable "alert_email" - A email address to receive cluster stats and alerts (default value 'later')
  - variable "release" - The release string matching the tar file name provided by ThoughtSpot.
  - variable "release_location" - The directory where you have downloaded the release tar
AWS environment specific variables:
  - variable "region" - AWS region where this would be provisioned
  - variable "vpc_subnet_id" - A valid subnet in your environment
  - variable "security_groups" - Security group to allow access to Thoughspot cluster
  - variable "ami_id" - The AMI id (public AMI from Thoughtspot copied to your region/account)

### Initialize terraform
As first step initialize terraform to get necessary binaries and setup backends
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
:point_right: **This step would as for a couple of interactive inputs**
1. Your confirmation for terraform to proceed with this change
2. password for admin user


### State file management
Terraform creates a file called terraform.tfstate which describes the provisioned infrastructure.
This file needs to be managed properly.
There are a number of ways to do it, which is not done in this repository.
https://blog.gruntwork.io/how-to-manage-terraform-state-28f5697e68fa
