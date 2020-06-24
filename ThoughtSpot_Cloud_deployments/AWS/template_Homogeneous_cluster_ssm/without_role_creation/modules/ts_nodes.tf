# Cluster node formation

data "aws_caller_identity" "current" {}


resource "aws_instance" "ts_cluster_instance" {
  count                       = var.no_of_instance
  ami                         = var.ami
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = var.vpc_security_group_ids
  iam_instance_profile        = var.instance_profile
  user_data                   = var.user_data

  ebs_block_device{
    device_name                 = "/dev/xvdb"
    volume_type                 = "gp2"
    volume_size                 = var.data_vol_size
    delete_on_termination       = true
    encrypted                   = false
  }
  ebs_block_device{
    device_name                 = "/dev/xvdc"
    volume_type                 = "gp2"
    volume_size                 = var.export_vol_size
    delete_on_termination       = true
    encrypted                   = false
  }
    ebs_block_device{
    device_name                 = "/dev/xvdd"
    volume_type                 = "gp2"
    volume_size                 = var.data_vol_size
    delete_on_termination       = true
    encrypted                   = false
  }
  root_block_device{
    volume_size               = var.root_vol_size
    delete_on_termination     = true
  }

  tags = {
        Name                  = "${var.name}-${count.index + 1}"
        User                  = "${data.aws_caller_identity.current.arn}"
        SSM_TAG               = var.name
  }
}

output "ts_host_ips" {
    value = aws_instance.ts_cluster_instance.*.private_ip
}

output "ts_inst_ids" {
    value = aws_instance.ts_cluster_instance.*.id
}
