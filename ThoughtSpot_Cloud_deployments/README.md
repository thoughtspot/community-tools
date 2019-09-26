# community-tools/ThoughtSpot_Cloud_deployments
This specific sub-repository contains a variety of tools that have been developed to assist in the deploying ThoughtSpot on a cloud platform.
This utility uses terraform and ansible to automate deployment of TS infrastructure and the cluster
  - Templates to deploy on AWS is available now.
  - Scripts for Azure and GCP will be added in the future.

Note that all tools are provided AS-IS according to the MIT license (see below).  While these have been
QAd, tested, and used in ThoughtSpot environments, every environment is different.  
Use these only if you know what you are doing.

If you have questions about the tools, please direct you questions to the ThoughtSpot community:  
http://community.thoughtspot.com.  

We hope you find these tools useful.  Please provide feedback in the Community along with suggestions
for improvements or additional tools.

>Copyright 2017 ThoughtSpot
>
>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
>files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
>modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
>Software is furnished to do so, subject to the following conditions:
>
>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
>OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
>BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
>OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for deploying TS on the cloud.

Before you start, a deployment host needs to be setup, which acts as the launching platform for the terraform and ansible tools.

So before you start, provision a VM that can access your cloud infrastructure.
This VM usually sits within the infrastructure and acts as a jumphost.
  - Should be able to access internet to get terraform plugins
  - Should be able to reach the intended target ip subnets planned for ThoughtSpot

### Contact support

Before you start, there are some Prerequisites that needs to be availed from ThoughtSpot Support.
  - ThoughtSpot release binary and the MD5checksum file (These needs to be copied to deployment host)
  - The cluster ID
  - Initial Login credentials to the cluster

### Setup the deployment host

Install these to kickstart the setup
```
$ sudo yum -y install ansible git
```

Clone this repo

```
$ git clone git@github.com:thoughtspot/community-tools.git
$ cd ./community-tools/ThoughtSpot_Cloud_deployments/deployment_server/
```

Run below command to setup your deployment host
```
$ ansible-playbook deployer.yaml
```

### Verify your cloud infrastructure setup.

Terraform can provision an entire infrastructure, but this process would require the Network and Security groups to be pre-created in your infrastructure.
So these components below should be already available in your environment and provided as an input parameter for the proceeding steps.

  - The AWS VPC where you will deploy ThoughtSpot
  - The relevant security groups required for the EC2 instances

### Setup the environment

Terraform needs to be able to access your cloud provider via API.
To facilitate this, setup the keys in the environment variables
(There are other methods which can be used to provide credentials, not covered in this)

For AWS:
$ export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$ export AWS_ACCESS_KEY_ID="yyyyyyyyyyyyyyyyy"

### Ready to start
We are now ready to proceed with the setup.
 - GO TO -> the respective cloud section under ./community-tools/ThoughtSpot_Cloud_deployments/
 - follow the instructions in the README.md for the type of cluster (eg template_Heterogeneous_cluster)
