# TS heterogeneous cluster
Terraform repository for TS heterogeneous cluster

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.
This repo contains terraform config tf code that is designed to provision a TS heterogeneous cluster.
See deployment for notes on how to deploy the project on a live system.

### Prerequisites
You would need to have the deployment host setup.
Please refer README.md under community-tools/ThoughtSpot_Cloud_deployments directory
:warning: Do not proceed with below steps if the deployment host is not setup properly.

### Reach the code

This specific code is available under
```
$ cd ./community-tools/ThoughtSpot_Cloud_deployments/AWS/template_Heterogeneous_cluster/install_workflow
```

## Provisioning new Infra
The environment specific values need to be setup in variable file.
Modify the variable file variables.tf accordingly
  - number_of_falcon          - number of falcon hosts to manage the database
  - number_of_metadata_nodes  - number of Callosum and sage hosts
  - cluster_name              - name of the cluster, tagged to each resources
  - cluster_id                - the cluster_id for this installation
  - alert_email               - email to send alerts from cluster
  - release                   - software release that will be installed
  - release_directory         - location on the deployment host where the release tar is available (+ MD5checksum)
  - number_of_falcon          - number of nodes for falcon
  - number_of_metadata_nodes  - number of nodes for callosum and sage
  - vol_size                  - size of disks for each vm
  - base_ami                  - AMI id shared for TS
  - vpc_subnet_id
  - security_groups
  - region

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

### State file management
Currently not setup. 
