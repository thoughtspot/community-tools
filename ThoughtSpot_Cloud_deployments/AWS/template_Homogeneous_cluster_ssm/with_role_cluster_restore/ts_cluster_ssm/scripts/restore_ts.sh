#!/bin/bash

set -xe

wait_file() {
  local file="$1"; shift
  local wait_seconds="$1"; shift

  until test $((wait_seconds--)) -eq 0 -o -f "$file" ; do sleep 1; done

  ((++wait_seconds))
}


wait_ready() {
  local file="$1"; shift
  local host_list="$1"; shift
  local wait_seconds="$1"; shift
  ssh_opts='-q -o StrictHostKeyChecking=no'
  ready=0
  until [[ $ready -eq 1 || $wait_seconds -eq 0 ]]
  do
    for HOST in $(awk 'NR == 3' $host_list)
    do
      if sudo -u admin bash -c "ssh $ssh_opts $HOST 'test -e $file'"; then
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

############################## BEGIN TS restoration ###########################
# Setup work dir
echo "Waiting for Current Instance to be setup"
KEY=/home/admin/restoration/start_restore_process
INST_DIR=/home/admin/restoration/
wait_file "$KEY" 7200 || {
  echo "Instance preparation has not completed after an hour. Exiting !!!"
  exit 1
}
echo "Instance setup completed"

# This file will be dynamically generated and copied during the terraform execution
# and will store it under the provided S3 bucket location
cd /home/admin/restoration/
aws s3 cp s3://aaron-sre/6.1.1-2.restore.ini ./6.1.1-2.restore.ini
echo "Restore config copied locally"

# Wait for all system to be ready
echo "Waiting for All Instances to be setup"
KEY=/home/admin/restoration/start_restore_process
HOST_LIST=./6.1.1-2.restore.ini
wait_ready "$KEY" "$HOST_LIST" 3600 || {
  echo "All instances preparation has not completed after an hour. Exiting !!!"
  exit 1
}

# Mount EFS volume
echo "Mounting EFS volume"
mkdir /export/backup
sudo mount -t nfs -o rsize=1048576,wsize=1048576,hard,timeo=600 192.168.7.183:/mnt/giantstore/Backups /export/backup

# Download the release tarball.
cd /home/admin/restoration/
sudo -u admin bash -c "/usr/local/scaligent/bin/tscli cluster restore /export/backup/sre_share/apple_test/full_backup < ./6.1.1-2.restore.ini"
echo "Cluster create completed"
sudo -u admin bash -c '/usr/local/scaligent/bin/tscli cluster status'
echo "Cluster ready"
############################## END TS restoration #############################
