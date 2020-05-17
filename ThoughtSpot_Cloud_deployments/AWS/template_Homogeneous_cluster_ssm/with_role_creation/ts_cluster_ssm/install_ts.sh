#!/bin/bash

set -xe

wait_file() {
  local file="$1"; shift
  local wait_seconds="${1:-10}"; shift # 10 seconds as default timeout

  until test $((wait_seconds--)) -eq 0 -o -f "$file" ; do sleep 1; done

  ((++wait_seconds))
}

############################## BEGIN TS Installation ###########################
# Setup work dir
echo "Waiting for Instance to be setup"
KEY=/home/admin/installation/start_install_process
INST_DIR=/home/admin/installation/
wait_file "$KEY" 7200 || {
  echo "Instance preparation has not completed after an hour. Exiting !!!"
  exit 1
}
echo "Instance setup completed"

# Download the release tarball.
cd /home/admin/installation/
aws s3 cp <TS_RELEASE_TARBALL_PATH_FROM_S3> ./<RELEASE>.tar.gz

# This file will be dynamically generated and copied during the terraform execution
# and will store it under the provided S3 bucket location
aws s3 cp s3://<S3_BUCKET_NAME>/<RELEASE>.install.ini ./<RELEASE>.install.ini
echo "Release copied to host"

# A buffer wait time
sleep 60m

# Download the release tarball.
cd /home/admin/installation/
sudo -u admin bash -c '/usr/local/scaligent/bin/tscli cluster create ./6.1.1-2.tar.gz < ./6.1.1-2.install.ini'
echo "Cluster create completed"
sudo -u admin bash -c '/usr/local/scaligent/bin/tscli cluster status'
echo "Cluster ready"
############################## END TS Installation #############################
