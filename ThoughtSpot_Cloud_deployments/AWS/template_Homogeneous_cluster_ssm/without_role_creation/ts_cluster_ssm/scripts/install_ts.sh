#!/bin/bash

set -xe

wait_file() {
  local file="$1"; shift
  local wait_seconds="${1:-10}"; shift # 10 seconds as default timeout

  until test $((wait_seconds--)) -eq 0 -o -f "$file" ; do sleep 1; done

  ((++wait_seconds))
}


wait_ready() {
  local file="$1"; shift
  local host_list="$1"; shift
  local wait_seconds="${1:-10}"; shift # 10 seconds as default timeout
  ssh_opts='-q -o StrictHostKeyChecking=no'
  ready=0
  until [[ $ready -eq 1 || $wait_seconds -eq 0 ]]
  do
    for HOST in `awk 'NR == 3' $host_list`
    do
      if sudo -u admin bash -c "ssh $ssh_opts $HOST "test -e $file""; then
        echo "$HOST Ready"
        ready=1
      else
	      echo "$HOST Not Ready"
	      ready=0
      fi
    done
    ((wait_seconds--))
  done
}

############################## BEGIN TS Installation ###########################
# Setup work dir
echo "Waiting for Current Instance to be setup"
KEY=/home/admin/installation/start_install_process
INST_DIR=/home/admin/installation/
wait_file "$KEY" 7200 || {
  echo "Instance preparation has not completed after an hour. Exiting !!!"
  exit 1
}
echo "Instance setup completed"

# Download the release tarball.
cd /home/admin/installation/
aws s3 cp s3://<S3_BUCKET_WITH_FOLDER>/<TS_RELEASE_TARBALL> ./<RELEASE>.tar.gz

# This file will be dynamically generated and copied during the terraform execution
# and will store it under the provided S3 bucket location. 
aws s3 cp s3://<S3_BUCKET>/<RELEASE>.install.ini ./<RELEASE>.install.ini
echo "Release copied to host"

# Wait for all system to be ready
echo "Waiting for All Instances to be setup"
KEY=/home/admin/installation/start_install_process
HOST_LIST=./<RELEASE>.install.ini
wait_ready "$KEY" "$HOST_LIST" 3600 || {
  echo "All instances preparation has not completed after an hour. Exiting !!!"
  exit 1
}

# Download the release tarball.
cd /home/admin/installation/
sudo -u admin bash -c '/usr/local/scaligent/bin/tscli cluster create ./<RELEASE>.tar.gz < ./<RELEASE>.install.ini'
echo "Cluster create completed"
sudo -u admin bash -c '/usr/local/scaligent/bin/tscli cluster status'
echo "Cluster ready"
############################## END TS Installation #############################
