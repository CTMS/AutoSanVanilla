#!/usr/bin/python3

import os
import subprocess
import sys


def run_command(command, check=True):
    """
    Run a shell command and optionally check for errors.
    """
    try:
        print(f"Running command: {command}")
        subprocess.run(command, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)


def is_package_installed(package_name):
    """
    Check if a package is already installed using dpkg-query.
    """
    try:
        result = subprocess.run(
            f"dpkg-query -W -f='${{Status}}' {package_name} 2>/dev/null | grep -q 'install ok installed'",
            shell=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking package '{package_name}' installation status: {e}")
        return False


def ensure_package_installed(package_name):
    """
    Ensure a specific APT package is installed. If not, install it.
    """
    if is_package_installed(package_name):
        print(f"Package '{package_name}' is already installed. Skipping installation.")
    else:
        print(f"Package '{package_name}' is not installed. Installing it now...")
        run_command(f"apt install -y {package_name}")


def ensure_kernel_module(module):
    """
    Ensure a specific kernel module is loaded. If not, attempt to load it with modprobe.
    """
    try:
        print(f"Checking if kernel module '{module}' is loaded...")
        result = subprocess.run(f"lsmod | grep -w {module}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Kernel module '{module}' is not loaded. Loading it now with modprobe...")
            run_command(f"modprobe {module}")
        else:
            print(f"Kernel module '{module}' is already loaded.")
    except Exception as e:
        print(f"Failed to check or load kernel module '{module}': {e}")
        sys.exit(1)


def main():
    # Save the original PATH
    old_path = os.environ['PATH']

    try:
        # Step 1: Remount /boot-pool as read-write
        print("Remounting /boot-pool as read-write...")
        run_command("mount -o remount,rw /boot-pool")

        # Step 2: Modify PATH temporarily
        print("Modifying PATH to temporarily enable apt and dpkg...")
        os.environ['PATH'] = "/usr/bin:/usr/sbin"

        # Step 3: Make apt and dpkg executable
        print("Making apt and dpkg executable...")
        run_command("chmod +x /bin/apt*")
        run_command("chmod +x /usr/bin/dpkg")

        # Step 4: Update APT
        print("Running apt update...")
        run_command("apt update")

        # Step 5: Ensure required packages are installed
        print("Ensuring required packages are installed...")
        required_packages = [
            "rdma-core",
            "mlnx-tools",
            "libmlx5-1",
            "libmlx5-dev",
            "infiniband-diags",
            "isert",
            "scst",
            "scst-dkms",
            "scstadmin",
            "ibutils"
        ]
        for package in required_packages:
            ensure_package_installed(package)

        # Step 6: Ensure required kernel modules are loaded
        print("Ensuring all required kernel modules are loaded...")
        required_modules = [
            "isert_scst",
            "rdma_cm",
            "ib_core",
            "mlx5_ib",   # Driver for Mellanox InfiniBand adapter
            "mlx5_core",
            "ib_uverbs",
            "mlxfw",
            "rdma_ucm",  # Additional module for RDMA
            "ib_umad",   # Management Datagram
            "ib_iser",   # iSER functionality
            "ib_ipoib",  # IP over InfiniBand
            "ib_cm"      # Communication Manager
        ]
        for module in required_modules:
            ensure_kernel_module(module)

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Step 7: Restore the original PATH
        print("Restoring the original PATH...")
        os.environ['PATH'] = old_path

        # Step 8: Remount /boot-pool as read-only
        print("Remounting /boot-pool as read-only for safety...")
        run_command("mount -o remount,ro /boot-pool")
        print("Script execution finished.")


if __name__ == "__main__":
    main()