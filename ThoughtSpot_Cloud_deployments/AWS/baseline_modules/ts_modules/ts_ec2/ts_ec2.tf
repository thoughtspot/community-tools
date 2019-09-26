
resource "aws_instance" "ts-ec2-instance" {
  count                       = "${var.number_of_instances}"
  ami                         = "${var.base_ami}"
  instance_type               = "${var.ts_instance_type}"
  monitoring                  = false
  subnet_id                   = "${var.vpc_subnet_id}"
  vpc_security_group_ids      = "${var.security_groups}"

  ebs_block_device{
    device_name                 = "/dev/sdb"
    volume_type                 = "gp2"
    volume_size                 = "${var.vol_size}"
    delete_on_termination       = true
    encrypted                   = false
  }
  ebs_block_device{
    device_name                 = "/dev/sdc"
    volume_type                 = "gp2"
    volume_size                 = "${var.vol_size}"
    delete_on_termination       = true
    encrypted                   = false
  }
  root_block_device{
    volume_size               = 200
    delete_on_termination     = true
  }

  tags = {
        Name                  = "${var.cluster_name}-${count.index + 1}"
        User                  = "${var.owner_tag}"
  }
}

output "ts_host_ip" {
    value = "${aws_instance.ts-ec2-instance.*.private_ip}"
}

output "ts_inst_id" {
    value = "${aws_instance.ts-ec2-instance.*.id}"
}
