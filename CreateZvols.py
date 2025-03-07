#!/usr/bin/python3

import os
import subprocess

# Function to execute system commands
def run_command(command):
    try:
        print(f"Running command: {command}")
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        exit(1)

def main():
    pool_name = "dpool"  # Assume the pool already exists
    zvol1_name = "lun16k"
    zvol1_blocksize = "16k"
    zvol2_name = "lun128k"
    zvol2_blocksize = "128k"

    # Prompt the user to specify ZVOL sizes
    zvol1_size = input(f"Enter the size for the ZVOL '{zvol1_name}' (e.g., 1G, 500M): ")
    zvol2_size = input(f"Enter the size for the ZVOL '{zvol2_name}' (e.g., 1G, 500M): ")

    # Check if the script is run as root
    if os.geteuid() != 0:
        print("This script must be run as root. Please use sudo.")
        exit(1)

    # Set ZFS pool properties (skipping pool creation, assuming it exists)
    print(f"Configuring ZFS pool '{pool_name}' with lz4 compression, atime off, dedup off, and sync=always...")
    run_command(f"zfs set compression=lz4 {pool_name}")
    run_command(f"zfs set atime=off {pool_name}")
    run_command(f"zfs set dedup=off {pool_name}")
    run_command(f"zfs set sync=always {pool_name}")

    # Create ZVOLs with the specified sizes and block sizes
    print(f"Creating ZVOL '{pool_name}/{zvol1_name}' with block size {zvol1_blocksize} and size {zvol1_size}...")
    run_command(f"zfs create -V {zvol1_size} -b {zvol1_blocksize} {pool_name}/{zvol1_name}")

    print(f"Creating ZVOL '{pool_name}/{zvol2_name}' with block size {zvol2_blocksize} and size {zvol2_size}...")
    run_command(f"zfs create -V {zvol2_size} -b {zvol2_blocksize} {pool_name}/{zvol2_name}")

    # Verify the configuration
    print("Verifying ZVOL properties...")
    run_command(f"zfs get all {pool_name}/{zvol1_name}")
    run_command(f"zfs get all {pool_name}/{zvol2_name}")

    print("ZVOL creation and configuration completed successfully.")

if __name__ == "__main__":
    main()