customer_name           = "appRestore1"
cluster_id              = "999X888199"
cluster_name            = "custALCluster01"
alert_email             = "alert@myalertemail.com"
release                 = "6.1.1-2"
subnet_id               = "subnet-7426922e"
vpc_id                  = "vpc-81b625f8"
ami                     = "ami-0d6621c01e8c2de2c"
vpc_security_group_ids  = ["sg-8898ecf7","sg-ec86f293"]
no_of_instance          = 4
instance_type           = "r4.16xlarge"
root_vol_size           = "100"
export_vol_size         = "200"
data_vol_size           = "400"
ssm_document_name       = "SSM-restore-01"
s3_bucket_name          = "aaron-sre"
user_data               = "user_data.sh"
s3_path_of_tar          = "aaron-sre"
offline_ansible_tar     = "6.1.1-2.offline.ansible.tar.gz"
mount_target_host       = "192.168.7.183"
mount_target_dir        = "/mnt/giantstore/Backups"
backup_subdir           = "sre_share/app_test/full_backup"