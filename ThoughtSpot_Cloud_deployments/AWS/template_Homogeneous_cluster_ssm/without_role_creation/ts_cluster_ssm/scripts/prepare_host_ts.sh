#!/bin/bash

############################## BEGIN TS Preparation ############################
set -xe

sudo chmod 777 /tmp

# Setup work dir
WORKDIR=/tmp/ansible
rm -rf $WORKDIR
mkdir -p $WORKDIR
cd $WORKDIR
echo "Directory set up"
# Download ansible release tarball.
aws s3 cp s3://<S3_BUCKET_WITH_FOLDER_IF_ANY>/<OFFLINE_ANSIBLE_TARBALL_FILE> ./

# Extract the tarball
tar -zxf <OFFLINE_ANSIBLE_TARBALL_FILE>
echo "Files staged"
# Run script for installing packages
sudo sed -i "s/localpkg_gpgcheck/# localpkg_gpgcheck/g" /etc/yum.conf
sudo touch /tmp/run_offline_log
sudo chmod 777 /tmp/run_offline_log
#sudo pip uninstall ansible -y
./run_offline.sh >> /tmp/run_offline_log 2>&1
echo "Packages installed"
# Make a copy of the inventory file
cp hosts.sample hosts.yaml

# Replace the ts_partition_name var in hosts file
TS_DISK=xvdc
TS_PARTITION_NAME=${TS_DISK}1
sed -i "s/xvda9/$TS_PARTITION_NAME/g" hosts.yaml
# Disk Partition. Should be consistent with $TS_PARTITION_NAME
sudo parted -s /dev/$TS_DISK mklabel gpt
sudo parted -s /dev/$TS_DISK mkpart primary xfs 0% 100%

# 1001:1001 is occupied by ssm-user, replace it in hosts.yaml
# Use a different, unused gid:uid
sed -i 's/1001/1003/g' hosts.yaml
echo "hosts.yaml setup"
# Run playbook
ansible-playbook -i hosts.yaml ts-amzn.yaml
echo "Ansible playbook completes"

INSTALL_DIR=/home/admin/installation/
rm -rf $INSTALL_DIR
mkdir -p $INSTALL_DIR
touch $INSTALL_DIR/start_install_process
sudo chmod 777 $INSTALL_DIR/start_install_process
echo "Directory set up for installation"

#Prepare disks for HDFS
sudo /usr/local/scaligent/bin/prepare_disks.sh

############################## END TS Preparation ##############################
