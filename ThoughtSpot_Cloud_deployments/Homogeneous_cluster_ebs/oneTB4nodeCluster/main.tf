
provider "aws" {
  /*
    This specify the region under which these resources are created.
    If any existing resources are specified and is not available under this
    region would cause terraform to error out.
  */
    region            = "${var.region}"
}

module "ts-instance" {
  /*
    This invokes the module available in ./baseline/ts_modules/ to create the
    ec2 instance.
      - number_of_instances is created
      - inst_size defines the type of the instance used
      - vpc_subnet_id defines the vpc subnet id where TS will be deployed
      - security_groups defined for access with the TS ec2 instances
      - # $vol_size is used for AMI without disk on the module ts_ec2
  */
  source              = "../baseline/ts_modules/ts_ec2_ami_ebs"
  customer_name       = "${var.customer_name}"
  ts_instance_type    = "${lookup(var.ts_instance_type,var.inst_size)}"
  number_of_instances = "${var.number_of_instances}"
  base_ami            = "${var.ami_id}"
  security_groups     = "${var.security_groups}"
  vpc_subnet_id       = "${var.vpc_subnet_id}"
  key_name            = "${var.key_name}"
  #vol_size            = "${var.vol_size}"
}

resource "local_file" "install_input" {
  /*
    We are building the input parameter file for ThoughtSpot installation
    This creates a local file install.ini with the four inputs needed during TS
    installation.
                cluster_name
                cluster_id
                ip_addr1 ip_addr1 ... ...
                alert_email
  */
  depends_on        = ["module.ts-instance"]
  content           = "${var.customer_name}\n${var.cluster_id}\n${join(" ", module.ts-instance.ts_host_ip)}\n${var.alert_email}\n"
  filename          = "install.ini"
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
              [all:vars]
  */
  depends_on        = ["local_file.install_input"]
  content           = "${templatefile("template_inventory.cfg", { ip_addrs = "${module.ts-instance.ts_host_ip}", user = "${var.ssh_user}", password = "${var.admin_password}" })}"
  filename          = "inventory.ini"
}

resource "null_resource" "running_ansible_playbook" {
  /*
    This is a resource that is used to invoke the local-exec porvisioner.
    Once we have the instances provisioned and the parameter file build, invoke
    ansible on the local deployment machine itself and kick-off the configuration
    and installation of ThoughtSpot.
  */
  depends_on        = ["local_file.ansible_inventory"]
  triggers = {
    ip              = "${module.ts-instance.ts_host_ip[0]}"
  }
  provisioner "local-exec" {
    /*
      Command to start ansible play.
      This asks for password to be used by ansible. Interactive step
    */
    command = "ANSIBLE_HOST_KEY_CHECKING=\"False\" ansible-playbook --ask-pass -i inventory.ini ${var.playbook} --extra-vars \"host='${module.ts-instance.ts_host_ip[0]}' release_loc='${var.release_location}' release='${var.release}'\""
  }
}

output "ts_host_ips" {
    description       = "The private IP address of the servers provisioned "
    value             = "${module.ts-instance.ts_host_ip}"
}
