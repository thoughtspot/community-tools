# SSM Document

resource "local_file" "generate_prepare_host_sh" {
  content           = templatefile("../ts_cluster_ssm/config_templates/prepare_host_ts.cfg", {
                                  offlineansiblefile = var.offline_ansible_tar,
                                  s3bucketwithsubfolder = var.s3_path_of_tar,
                                  release = var.release
                                  })
  filename          = "../ts_cluster_ssm/scripts/prepare_host_ts.sh"
}

resource "aws_s3_bucket_object" "file_upload_setup" {
  depends_on    = [local_file.generate_prepare_host_sh]
  bucket        = var.s3_bucket_name
  key           = "prepare_host_ts.sh"
  source        = "../ts_cluster_ssm/scripts/prepare_host_ts.sh"
}

resource "aws_ssm_document" "ssm_doc_for_tssetup" {
  depends_on    = [aws_s3_bucket_object.file_upload_setup]
  name            = "${var.ssm_document_name}-setup"
  document_type   = "Command"
  document_format = "JSON"
  tags            = merge({ "Name" = "${var.ssm_document_name}-setup" }, var.tags)

  content         = <<DOC
{
  "schemaVersion": "2.2",
  "description": "Prepare node for TS",
  "parameters": {
     "executionTimeout":{
        "type": "String",
        "default": "7200"
      }
  },
  "mainSteps": [
    {
      "action": "aws:runShellScript",
      "name": "default",
      "inputs": {
        "timeoutSeconds": "{{ executionTimeout }}",
        "runCommand": [
            "mkdir -p /tmp/setup",
            "cd /tmp/setup",
            "aws s3 cp s3://${var.s3_bucket_name}/prepare_host_ts.sh ./prepare_host_ts.sh",
            "chmod +x ./prepare_host_ts.sh",
            "./prepare_host_ts.sh >> /tmp/setup/ssm_doc_setup_log 2>&1"
        ]
      }
    }
  ]
}
DOC
}


# SSM Document association
resource "aws_ssm_association" "default_setup" {
  name    = aws_ssm_document.ssm_doc_for_tssetup.name

  targets {
    key    = "InstanceIds"
    values = aws_instance.ts_cluster_instance.*.id
  }

  output_location {
    s3_bucket_name = var.s3_bucket_name
  }
}


resource "local_file" "generate_restore_sh" {
  content           = templatefile("../ts_cluster_ssm/config_templates/restore_ts.cfg", {
                                  s3bucketwithsubfolder = var.s3_path_of_tar,
                                  s3bucket = var.s3_bucket_name,
                                  release = var.release,
                                  mount_target_host = var.mount_target_host,
                                  mount_target_dir = var.mount_target_dir,
                                  backup_subdir = var.backup_subdir
                                  })
  filename          = "../ts_cluster_ssm/scripts/restore_ts.sh"
}

resource "aws_s3_bucket_object" "file_upload_restore" {
  depends_on    = [local_file.generate_prepare_host_sh]
  bucket        = var.s3_bucket_name
  key           = "restore_ts.sh"
  source        = "../ts_cluster_ssm/scripts/restore_ts.sh"
}

resource "aws_ssm_document" "ssm_doc_for_tsrestore" {
  depends_on    = [aws_s3_bucket_object.file_upload_restore]
  name            = "${var.ssm_document_name}-restore"
  document_type   = "Command"
  document_format = "JSON"
  tags            = merge({ "Name" = "${var.ssm_document_name}-restore" }, var.tags)

  content         = <<DOC
{
  "schemaVersion": "2.2",
  "description": "Restoring TS Cluster",
  "parameters": {
     "executionTimeout":{
        "type": "String",
        "default": "7200"
      }
  },
  "mainSteps": [
    {
      "action": "aws:runShellScript",
      "name": "default",
      "inputs": {
        "timeoutSeconds": "{{ executionTimeout }}",
        "runCommand": [
            "mkdir -p /tmp/restore",
            "cd /tmp/restore",
            "aws s3 cp s3://${var.s3_bucket_name}/restore_ts.sh ./restore_ts.sh",
            "chmod +x ./restore_ts.sh",
            "./restore_ts.sh >> /tmp/restore/ssm_doc_restore_log 2>&1"
        ]
      }
    }
  ]
}
DOC
}


# SSM Document association
resource "aws_ssm_association" "default_restore" {
  name    = aws_ssm_document.ssm_doc_for_tsrestore.name

  targets {
    key    = "InstanceIds"
    values = [aws_instance.ts_cluster_instance[0].id]
  }

  output_location {
    s3_bucket_name = var.s3_bucket_name
  }
}



output "ts_setup_document_status" {
  value       = aws_ssm_document.ssm_doc_for_tssetup.status
  description = "The current status of the document."
}

output "ts_setup_document_name" {
  value       = aws_ssm_document.ssm_doc_for_tssetup.name
  description = "The name of the document."
}
output "ts_restore_document_status" {
  value       = aws_ssm_document.ssm_doc_for_tsrestore.status
  description = "The current status of the document."
}

output "ts_restore_document_name" {
  value       = aws_ssm_document.ssm_doc_for_tsrestore.name
  description = "The name of the document."
}
