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
        run_command(f"apt install -y -f {package_name}")


def load_kernel_module(module):
    """
    Load a specific kernel module using modprobe.
    """
    try:
        print(f"Loading kernel module '{module}'...")
        run_command(f"modprobe {module}")
        print(f"Kernel module '{module}' loaded successfully.")
    except Exception as e:
        print(f"Failed to load kernel module '{module}': {e}")
        sys.exit(1)


def unload_kernel_module(module):
    """
    Unload a specific kernel module using modprobe -r.
    """
    try:
        print(f"Unloading kernel module '{module}'...")
        run_command(f"modprobe -r {module}")
        print(f"Kernel module '{module}' unloaded successfully.")
    except Exception as e:
        print(f"Failed to unload kernel module '{module}': {e}")


def reload_kernel_module(module):
    """
    Reload a specific kernel module by first unloading it and then loading it again.
    """
    unload_kernel_module(module)
    load_kernel_module(module)


def find_boot_pool_root_from_df():
    """
    Find the boot-pool/ROOT/<version>/usr path dynamically by parsing 'df -h' output.

    :return: The full path to boot-pool/ROOT/<version>/usr if found, else None.
    """
    try:
        # Run `df -h` command and capture the output
        result = subprocess.run(['df', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        # Parse the output line by line
        for line in result.stdout.splitlines():
            # Look for lines containing boot-pool/ROOT and /usr
            if "boot-pool/ROOT" in line and "/usr" in line:
                # Extract the mount path (usually the last column in df -h output)
                parts = line.split()  # Split the line into components
                mount_path = parts[0]  # The mount point is in the last column
                return mount_path

    except subprocess.CalledProcessError as e:
        print(f"Error running 'df -h': {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None


def ensure_required_packages_installed():
    """
    Ensure a list of required packages is installed.
    If a package fails, the script will continue to the next one.
    """
    required_packages = [
        "byobu",            # Terminal management tool
        "rdma-core",        # RDMA user libraries and drivers
        "libmlx5-1",        # Mellanox ConnectX-4/5 InfiniBand/Ethernet libraries
        "infiniband-diags", # Diagnostic tools for InfiniBand
        "ibutils",          # InfiniBand utilities
        "ibverbs-providers",# RDMA Verbs providers for user-level verbs
        "ibverbs-utils",    # RDMA Verbs utilities for troubleshooting
        "multipath-tools",
        "open-iscsi",
        "mstflint",          # Mellanox firmware burning and query utility
    ]

    for package in required_packages:
        try:
            ensure_package_installed(package)
        except Exception as e:
            print(f"Failed to process package '{package}'. Error: {e}")


def reload_all_required_kernel_modules():
    """
    Reload all required kernel modules.
    """
    required_modules = [
        "isert_scst",       # SCSI target framework for iSER
        "rdma_cm",          # RDMA Communication Manager
        "ib_core",          # InfiniBand core support
        "mlx5_ib",          # Driver for Mellanox InfiniBand adapter
        "mlx5_core",        # Mellanox ConnectX-4/5 drivers
        "ib_uverbs",        # User-level verbs for RDMA
        "mlxfw",            # Mellanox firmware updates
        "rdma_ucm",         # RDMA CM user-space module
        "ib_umad",          # Management Datagram
        "ib_iser",          # iSER functionality
        "ib_ipoib",         # IP over InfiniBand
        "ib_cm"             # InfiniBand Communication Manager
    ]
    for module in required_modules:
        print(f"Reloading kernel module: {module}")
        reload_kernel_module(module)


def restart_scst_service():
    """
    Restart the SCST service (systemctl restart scst.service).
    """
    try:
        print("Restarting SCST service...")
        run_command("systemctl restart scst.service")
        print("SCST service restarted successfully.")
    except Exception as e:
        print(f"Failed to restart SCST service: {e}")
        sys.exit(1)


def get_user_input():
    """
    Prompt the user to choose to proceed or go back to the main menu.
    """
    print("\nWhat this script will do:")
    print("==========================")
    print("1. Ensure the required packages are installed.")
    print("2. Reload required kernel modules.")
    print("3. Restart the SCST service (scst.service).")
    print("==========================")
    print("\nOptions:")
    print("1. Proceed with these actions")
    print("2. Back to the main menu\n")

    while True:
        try:
            user_input = int(input("Enter your choice (1 or 2): ").strip())
            if user_input in [1, 2]:
                return user_input
            else:
                print("Invalid input. Please enter 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a numeric value (1 or 2).")


def main():
    # Save the original PATH
    old_path = os.environ['PATH']

    # Get user input for proceeding or going back to the main menu
    choice = get_user_input()
    if choice == 2:
        print("Returning to the main menu. No actions will be taken.")
        sys.exit(0)

    try:
        # Step 1: Dynamically find the boot-pool path
        boot_pool_path = find_boot_pool_root_from_df()
        if not boot_pool_path:
            print("Error: Could not find the boot-pool/ROOT/<version>/usr path.")
            sys.exit(1)

        print(f"Found boot-pool path: {boot_pool_path}")

        # Step 2: Remount the target boot-pool directory as read-write
        print(f"Remounting {boot_pool_path} as read-write...")
        run_command(f"mount -o remount,rw {boot_pool_path}")

        # Step 3: Modify PATH temporarily
        print("Modifying PATH to temporarily enable apt and dpkg...")
        os.environ['PATH'] = "/usr/bin:/usr/sbin"

        # Step 4: Make apt and dpkg executable
        print("Making apt and dpkg executable...")
        run_command("chmod +x /bin/apt*")
        run_command("chmod +x /usr/bin/dpkg")

        # Step 5: Ensure required packages are installed
        print("Ensuring required packages are installed...")
        ensure_required_packages_installed()

        # Step 6: Reload all required kernel modules
        print("Reloading all required kernel modules...")
        reload_all_required_kernel_modules()

        # Step 7: Restart SCST service
        print("Restarting SCST service...")
        restart_scst_service()

        print("All required packages are ensured, kernel modules reloaded, and SCST service restarted!")

    finally:
        # Restore the original PATH
        os.environ['PATH'] = old_path


if __name__ == "__main__":
    main()