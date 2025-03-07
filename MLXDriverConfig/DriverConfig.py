#!/bin/python3
import os
import subprocess
import re

def run_command(command):
    """
    Execute a shell command and return the output.
    """
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(command)}\nError: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command {command}: {e}")
        return None

def get_mellanox_devices_truenas():
    """
    Identify Mellanox devices on TrueNAS using lspci.
    """
    print("Looking for Mellanox devices on TrueNAS...")
    lspci_output = run_command(["lspci", "-v"])
    if lspci_output is None:
        print("Failed to retrieve device list using lspci.")
        return []

    devices = []
    for line in lspci_output.splitlines():
        if "Mellanox" in line:
            # Parse the device ID from the lspci output
            match = re.match(r"^(\S+).*Mellanox", line)
            if match:
                devices.append(match.group(1))

    return devices

def check_and_set_mellanox_device(binary_path, is_truenas):
    """
    Check Mellanox devices and their settings, and set values if they do not match.
    Adjusts the command paths and device detection method based on the system type.
    """
    system_requires_reboot = False  # Track if a reboot is needed

    # Get Mellanox devices
    if is_truenas:
        devices = get_mellanox_devices_truenas()
    else:
        mst_status_output = run_command([os.path.join(binary_path, "mst"), "status"])
        if mst_status_output is None:
            print("Failed to retrieve Mellanox device status.")
            return system_requires_reboot
        print("mst status output:\n", mst_status_output)

        # Parse devices from the `mst status` output
        devices = []
        for line in mst_status_output.splitlines():
            if "/dev/mst/" in line:
                devices.append(line.split()[0])

    if not devices:
        print("No Mellanox devices found.")
        return system_requires_reboot

    print(f"Found Mellanox devices: {devices}")

    # Define required settings and their expected values
    required_settings = {
        "SAFE_MODE": "False(0)",
        "NUM_OF_VFS": "16",
        "VF_VPD_ENABLE": "True(1)",
        "SRIOV_EN": "True(1)",
        "NUM_PF_MSIX": "64",
        "NUM_VF_MSIX": "8",
        "LINK_TYPE_P1": "ETH(2)",
        "LINK_TYPE_P2": "ETH(2)",
        "EXP_ROM_UEFI_x86_ENABLE": "True(1)",
        "UEFI_HII_EN": "True(1)"
    }

    command_prefix = [binary_path + "/mlxconfig"] if not is_truenas else [binary_path + "/mstconfig"]

    # Check settings for each device and set them if needed
    for device in devices:
        print(f"\nChecking settings for device: {device}")
        query_command = command_prefix + (["-d", device, "q"] if not is_truenas else ["-d", device])
        mlxconfig_output = run_command(query_command)
        if mlxconfig_output is None:
            print(f"Failed to retrieve settings for device {device}.")
            continue

        print(f"mlxconfig output for {device}:\n", mlxconfig_output)

        # Track if settings need updates
        settings_to_update = []

        # Check each required parameter
        for key, expected_value in required_settings.items():
            match = re.search(fr"{key}\s+([^\s]+)", mlxconfig_output)
            if match:
                current_value = match.group(1)
                if current_value == expected_value:
                    print(f"{key}: {current_value} (OK)")
                else:
                    print(f"{key}: {current_value} (Expected: {expected_value})")
                    settings_to_update.append((key, expected_value))
            else:
                print(f"{key}: Not found in mlxconfig output (Expected: {expected_value})")
                settings_to_update.append((key, expected_value))

        # Update settings if required
        if settings_to_update:
            print(f"Updating settings for device {device}...")
            for key, value in settings_to_update:
                # Remove the "(value)" part from the expected value for use in the set command
                set_value = value.split("(")[1][:-1]
                set_command = command_prefix + (["-d", device, "set", f"{key}={set_value}"] if not is_truenas else [f"-d {device}", f"{key}={set_value}"])
                set_output = run_command(set_command)
                if set_output is not None:
                    print(f"Set {key} to {value}: {set_output}")

            # Apply the new configuration on ESXi; this step isn't needed on TrueNAS
            if not is_truenas:
                apply_command = command_prefix + ["-d", device, "apply", "-y"]
                apply_output = run_command(apply_command)
                if apply_output is not None:
                    print(f"Applied new settings for device {device}: {apply_output}")

            # Mark a reboot as required due to settings changes
            system_requires_reboot = True
        else:
            print(f"All settings for device {device} are already correct.")

    return system_requires_reboot

def main():
    # Ask the user for the system type
    system = input("Which system are you on? (Enter 'ESXi' or 'TrueNAS'): ").strip().lower()

    if system == "esxi":
        binary_path = "/opt/mellanox/bin"
        reboot_required = check_and_set_mellanox_device(binary_path, is_truenas=False)
    elif system == "truenas":
        binary_path = "/usr/bin"
        reboot_required = check_and_set_mellanox_device(binary_path, is_truenas=True)
    else:
        print("Invalid input. Please enter 'ESXi' or 'TrueNAS'.")
        return

    # Prompt for reboot if changes were applied
    if reboot_required:
        print("\nSystem changes require a reboot to take effect. Please reboot the system now.")
    else:
        print("\nNo changes were made, no reboot is necessary.")

if __name__ == "__main__":
    main()