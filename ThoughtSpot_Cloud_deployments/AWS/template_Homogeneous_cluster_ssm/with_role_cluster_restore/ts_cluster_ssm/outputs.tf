
output "TS_SETUP_ssm_document_status" {
  value = module.ts_cluster_ssm.ts_setup_document_status
}

output "TS_RESTORE_ssm_document_status" {
  value = module.ts_cluster_ssm.ts_restore_document_status
}

output "cluster_instance_ids" {
  value = module.ts_cluster_ssm.ts_inst_ids
}

output "cluster_instance_private_ips" {
  value = module.ts_cluster_ssm.ts_host_ips
}
