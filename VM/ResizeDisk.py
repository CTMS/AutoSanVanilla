#!/bin/python3

import os
import subprocess
import sys


def run_command(command, shell=True):
    """Utility function to run shell commands."""
    try:
        result = subprocess.run(command, shell=shell, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error message: {e.stderr.decode().strip()}")
        sys.exit(1)


def list_partitions():
    """Lists all partitions and allows the user to select one."""
    print("\nListing all available partitions:")
    lsblk_output = run_command("lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT")
    print(lsblk_output)
    print("\nNote: Partition names usually look like 'sda1', 'sda2', etc.")

    while True:
        partition = input("Enter the partition name you want to resize (e.g., sda3): ").strip()
        if run_command(f"lsblk | grep -w {partition}") != "":
            return f"/dev/{partition}"
        else:
            print(f"Invalid partition name: {partition}. Please try again.")


def main():
    print("Starting the disk resizing process...\n")

    # Step 1: List partitions and let the user choose one
    full_partition_path = list_partitions()
    print(f"\nYou have selected the partition: {full_partition_path}")

    # Extract device name (e.g., sda) from the full path
    device = full_partition_path.replace("/dev/", "").rstrip("0123456789")

    print(f"\nRescanning the device: /sys/block/{device}/device/rescan")
    # Step 2: Rescan the device
    run_command(f"echo 1 | sudo tee /sys/block/{device}/device/rescan")

    print("\nResizing the partition with parted...")
    # Step 3: Resize the partition using parted
    run_command(f"sudo parted /dev/{device} resizepart {full_partition_path[-1]} 100%")

    print("\nResizing the physical volume...")
    # Step 4: Resize the physical volume
    run_command(f"sudo pvresize {full_partition_path}")

    # Step 5: Check if the filesystem is LVM or XFS
    while True:
        fs_type_choice = input("\nIs the system using LVM or XFS? (type 'lvm' or 'xfs'): ").strip().lower()
        if fs_type_choice in ["lvm", "xfs"]:
            break
        else:
            print("Invalid input. Please type 'lvm' or 'xfs'.")

    if fs_type_choice == "lvm":
        lv_path = input("Enter the logical volume path (e.g., /dev/mapper/ubuntu--vg-ubuntu--lv): ").strip()
        print("\nExtending the Logical Volume...")
        run_command(f"sudo lvextend -l +100%FREE {lv_path}")

        # Step 6: Detect the filesystem type
        fs_type = run_command(f"lsblk -no FSTYPE {full_partition_path}").strip()
        if fs_type == "ext4":
            print("\nResizing the ext4 filesystem...")
            run_command(f"sudo resize2fs {lv_path}")
        elif fs_type == "xfs":
            mount_point = input("Enter the mount point for the XFS filesystem (e.g., /mnt): ").strip()
            print("\nGrowing the XFS filesystem...")
            run_command(f"sudo xfs_growfs {mount_point}")
            print("\nGetting XFS information...")
            run_command(f"sudo xfs_info {full_partition_path}")
        else:
            print("Unsupported filesystem type! Exiting.")
            sys.exit(1)
    elif fs_type_choice == "xfs":
        mount_point = input("Enter the mount point for the XFS filesystem (e.g., /mnt): ").strip()
        print("\nGrowing the XFS filesystem...")
        run_command(f"sudo xfs_growfs {mount_point}")
        print("\nGetting XFS information...")
        run_command(f"sudo xfs_info {full_partition_path}")

    # Step 7: Display the final disk state
    print("\nFinal disk state:")
    run_command("lsblk -o NAME,SIZE,LOG-SEC,PHY-SEC,OPT-IO,RA,TYPE,FSTYPE,MOUNTPOINTS,PATH,ID-LINK")

    print("\nProcess completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()