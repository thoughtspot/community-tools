#!/bin/bash

# Create a virtual environment
python3 -m venv myenv

# Activate the virtual environment
source myenv/bin/activate

dependencies=(
    ldap3
    requests
    datetime
    'urllib3<2.0'
)

# Upgrade pip
pip install --upgrade pip

# Install dependencies
for package in "${dependencies[@]}"; do
    pip install "$package";
done
