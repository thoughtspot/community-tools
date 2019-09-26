
provider "aws" {
    region = "${var.region}"
}

module "falcon_instances" {
  /*
    This invokes the module available in ./baseline/ts_modules/ to create the
    ec2 instance.
      - number_of_instances is created
      - inst_size defines the type of the instance used
      - vpc_subnet_id defines the vpc subnet id where TS will be deployed
      - security_groups defined for access with the TS ec2 instances
      - iam_instance_profile that has permissions for the ec2 instance to S3
  */
  source              = "../../baseline_modules/ts_modules/ts_ec2"
  cluster_name        = "${var.cluster_name}-falcon"
  ts_instance_type    = "${lookup(var.ts_instance_type, "falcon")}"
  number_of_instances = "${var.number_of_falcon}"
  base_ami            = "${var.base_ami}"
  vol_size            = "${var.vol_size}"
  security_groups     = "${var.security_groups}"
  vpc_subnet_id       = "${var.vpc_subnet_id}"
  owner_tag           = "${var.owner_tag}"
}
module "metadata_instances" {
  source              = "../../baseline_modules/ts_modules/ts_ec2"
  cluster_name        = "${var.cluster_name}-metadata"
  ts_instance_type    = "${lookup(var.ts_instance_type, "metadata")}"
  number_of_instances = "${var.number_of_metadata_nodes}"
  base_ami            = "${var.base_ami}"
  vol_size            = "${var.vol_size}"
  security_groups     = "${var.security_groups}"
  vpc_subnet_id       = "${var.vpc_subnet_id}"
  owner_tag           = "${var.owner_tag}"
}

resource "local_file" "install_input" {
  /*
    We are building the input parameter file for ThoughtSpot installation.
    This creates a local file install.ini with the five inputs needed during TS
    installation with S3 enabled cluster.
                cluster_name
                cluster_id
                ip_addr1 ip_addr1 ... ...
                alert_email
    This file will be used by the ThoughtSpot installer on the cluster nodes
  */
  depends_on        = ["module.falcon_instances", "module.metadata_instances"]
  content           = "${templatefile("templates/install.cfg", { cluster_name = "${var.cluster_name}", cluster_id = "${var.cluster_id}", ip_addrs = "${join(" ", concat(module.falcon_instances.ts_host_ip, module.metadata_instances.ts_host_ip))}", alert_email = "${var.alert_email}" })}"
  filename          = "config/install.ini"
}

resource "local_file" "ansible_inventory" {
  /*
  We are building the ansible inventory file based on the ip's provisioned for
  the ec2 instances
              [tscluster]
              ip_addr1
              ip_addr2
              ...
              [tsinstall]
              ip_addr1
              [tsinstall:vars]
              host=ip_addr1
  */
  depends_on        = ["local_file.install_input"]
  content           = "${templatefile("templates/inventory.cfg", { ip_addrs = "${concat(module.falcon_instances.ts_host_ip, module.metadata_instances.ts_host_ip)}", release_loc = "${var.release_directory}", release = "${var.release}", scheduling_policy="${var.scheduling_policy}" })}"
  filename          = "config/install_inventory.ini"
}

resource "local_file" "heterogeneous_service_labelling" {
  /*
    This is a resource that is used to generate the service labelling config file.
  */
  depends_on        = ["local_file.ansible_inventory"]
  content           = "${templatefile("templates/labels.cfg", { first_node = "${module.falcon_instances.ts_host_ip[0]}", falcon_nodes = "${slice(module.falcon_instances.ts_host_ip,1,length(module.falcon_instances.ts_host_ip))}", other_nodes = "${module.metadata_instances.ts_host_ip}" })}"
  filename          = "config/service_label.config"
}

resource "local_file" "heterogeneous_service_proto" {
  /*
    This is a resource that is used to generate the service labelling config file. (for 5.3.1)
  */
  depends_on        = ["local_file.ansible_inventory"]
  content           = "${templatefile("templates/labels_proto.cfg", { falcon_nodes = "${module.falcon_instances.ts_host_ip}", other_nodes = "${module.metadata_instances.ts_host_ip}" })}"
  filename          = "config/service_labels_proto.config"
}

resource "null_resource" "running_ansible_playbook" {
  /*
    This is a resource that is used to invoke the local-exec porvisioner.
    Once we have the instances provisioned and the parameter file build, invoke
    ansible on the local deployment machine itself and kick-off the configuration
    and installation of ThoughtSpot.
  */
  depends_on        = ["local_file.heterogeneous_service_labelling"]
  triggers = {
    ip              = "${module.falcon_instances.ts_host_ip[0]}"
  }
  provisioner "local-exec" {
    /*
      We use the default admin account whose password will be prompted when it is run
      Password is needed since the key gets changed after cluster installation
    */
    command = "ANSIBLE_HOST_KEY_CHECKING=\"False\" ansible-playbook -u ${var.ssh_user} --ask-pass -i config/install_inventory.ini ${var.playbook} "
  }
}

output "ts_host_ips" {
    description       = "The private IP address of the servers provisioned "
    value             = "${concat(module.falcon_instances.ts_host_ip, module.metadata_instances.ts_host_ip)}"
}
