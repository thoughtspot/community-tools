
terraform {
  required_version = "~> 0.12.24"
}

data "aws_s3_bucket" "selected_s3" {
  bucket = var.s3_bucket_name
}

module "ts_cluster_ssm" {
  source                        = "../modules/"

  name                          = var.cluster_name
  instance_type                 = var.instance_type
  no_of_instance                = var.no_of_instance
  subnet_id                     = var.subnet_id
  vpc_id                        = var.vpc_id
  ami                           = var.ami
  vpc_security_group_ids        = var.vpc_security_group_ids
  user_data                     = file("${path.module}/${var.user_data}")
  root_vol_size                 = var.root_vol_size
  export_vol_size               = var.export_vol_size
  data_vol_size                 = var.data_vol_size
  instance_profile              = var.instance_profile
  ssm_document_name             = var.ssm_document_name
  s3_bucket_name                = var.s3_bucket_name
  s3_path_of_tar                = var.s3_path_of_tar
  offline_ansible_tar           = var.offline_ansible_tar
  release_tar                   = var.release_tar
  release                       = var.release
  description                   = var.description

  tags = {
    Environment = "prod"
  }
}


resource "local_file" "install_input" {
    content     = "${var.cluster_name}\n${var.cluster_id}\n${join(" ", module.ts_cluster_ssm.ts_host_ips)}\n${var.alert_email}\n"
    filename    = "./out/${var.release}.install.ini"
}

resource "local_file" "ansible_inventory" {
  depends_on        = [local_file.install_input]
  content           = templatefile("./config_templates/inventory.cfg", {
                                  ip_addrs = "${module.ts_cluster_ssm.ts_host_ips}",
                                  release = "${var.release}"
                                  })
  filename          = "./out/ts_host_inventory.ini"
}


resource "aws_s3_bucket_object" "file_upload" {
  depends_on    = [local_file.install_input]
  bucket        = var.s3_bucket_name
  key           = "${var.release}.install.ini"
  source        = "${path.module}/out/${var.release}.install.ini"
}
