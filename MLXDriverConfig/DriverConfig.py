#!/bin/python3
import os
import re
import subprocess


def run_command(command, timeout=30):
    """
    Executes a shell command and returns the output.
    Provides safe error handling and timeouts.
    """
    try:
        print(f"Executing command: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(command)}\nError: {result.stderr.strip()}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(command)}")
    except Exception as e:
        print(f"Unexpected error while running command {' '.join(command)}: {e}")
    return None


def get_mellanox_devices_truenas():
    """
    Identify Mellanox devices on TrueNAS using lspci.
    """
    print("Looking for Mellanox devices on TrueNAS...")
    lspci_output = run_command(["lspci", "-v"])
    if not lspci_output:
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


def parse_mst_devices(output):
    """
    Parse device list from `mst status` command output.
    """
    try:
        lines = output.splitlines()
        # Assume lines after the first two contain device information
        devices = [line.strip() for line in lines[2:] if line.strip()]
        return devices
    except Exception as e:
        print(f"Error parsing `mst status` output: {e}")
        return []


def get_mellanox_devices(binary_path, is_truenas):
    """
    Retrieves Mellanox devices based on the system type (TrueNAS or generic Linux).
    """
    if is_truenas:
        return get_mellanox_devices_truenas()
    else:
        # Use `mst status` for non-TrueNAS systems
        mst_status_output = run_command([os.path.join(binary_path, "mst"), "status"])
        if not mst_status_output:
            print("Failed to retrieve Mellanox device status.")
            return []

        print("mst status output:")
        print(mst_status_output)
        return parse_mst_devices(mst_status_output)


def retrieve_device_settings(device, binary_path, is_truenas):
    """
    Retrieves the current settings for a Mellanox device.
    """
    command_prefix = [os.path.join(binary_path, "mstconfig")] if is_truenas else [os.path.join(binary_path, "mlxconfig")]
    query_command = command_prefix + (["-d", device, "q"] if not is_truenas else ["-d", device])
    return run_command(query_command)


def update_device_settings(device, required_settings, current_settings, command_prefix):
    """
    Updates Mellanox device settings when they do not match required values.
    If a setting is not found, it is skipped, and the user is notified.
    """
    print(f"Checking settings for device: {device}")
    settings_to_update = []

    # Check if settings need to be updated
    for setting, expected_value in required_settings.items():
        # Match the setting's current value in the output
        match = re.search(fr"{setting}\s+([^\s]+)", current_settings)
        if match:
            current_value_raw = match.group(1)  # Extract raw value (e.g., 'False(0)', 'True(1)', '16')

            # Extract the numeric value for comparison (e.g., 'False(0)' → '0', 'True(1)' → '1')
            current_value_numeric = re.search(r"\((\d+)\)", current_value_raw)
            if current_value_numeric:
                current_value = current_value_numeric.group(1)  # Get numeric component
            else:
                current_value = current_value_raw  # Fall back to raw value if no numeric value

            # Compare values as strings
            expected_value = str(expected_value)  # Ensure expected value is a string
            if current_value == expected_value:
                print(f"{setting}: {current_value_raw} (OK)")
            else:
                print(f"{setting}: {current_value_raw} (Expected: {expected_value})")
                settings_to_update.append((setting, expected_value))
        else:
            # Notify the user that the setting was not found and skip updating it
            print(f"{setting}: Not found in settings (Cannot update this setting)")

    # Apply updates if necessary
    if settings_to_update:
        print(f"Updating settings for device: {device}")
        update_command = command_prefix + ["-d", device, "-y", "set"]
        for setting, value in settings_to_update:
            update_command.append(f"{setting}={value}")  # Only the value is passed

        print(f"Update command: {' '.join(update_command)}")
        result = run_command(update_command)
        if result:
            print(f"Settings updated successfully for device: {device}")
            return True
        else:
            print(f"Failed to update settings for device: {device}")
            return False
    else:
        print(f"No settings need to be changed for device: {device}")
    return True


def check_and_configure_mellanox_devices(binary_path, is_truenas):
    """
    Checks Mellanox devices and their settings and applies necessary configuration adjustments.
    """
    system_requires_reboot = False  # Track if a reboot is needed
    devices = get_mellanox_devices(binary_path, is_truenas)

    if not devices:
        print("No Mellanox devices found!")
        print("Ensure Mellanox drivers are installed and the hardware is connected.")
        return system_requires_reboot

    print(f"Found Mellanox devices: {devices}")

    # Define required settings and their expected values
    required_settings = {
        "SAFE_MODE_ENABLE": "0",
        "NUM_OF_VFS": "16",
        "VF_VPD_ENABLE": "1",
        "SRIOV_EN": "1",
        "NUM_PF_MSIX": "64",
        "NUM_VF_MSIX": "8",
        "LINK_TYPE_P1": "2",
        "LINK_TYPE_P2": "2",
        "EXP_ROM_UEFI_x86_ENABLE": "1",
        "UEFI_HII_EN": "1",
        "EXP_ROM_PXE_ENABLE": "1"  # Example setting
    }

    command_prefix = [os.path.join(binary_path, "mstconfig")] if is_truenas else [os.path.join(binary_path, "mlxconfig")]

    # Process each device
    for device in devices:
        current_settings = retrieve_device_settings(device, binary_path, is_truenas)
        if current_settings:
            updated = update_device_settings(device, required_settings, current_settings, command_prefix)
            if updated:
                system_requires_reboot = True

    return system_requires_reboot


def main():
    """
    Entry point for configuring Mellanox devices.
    """
    print("Mellanox Driver Configuration Tool")

    # Determine the system type
    is_truenas = input("Are you configuring a TrueNAS system? (yes/no): ").strip().lower() in ["yes", "y"]

    # Set default binary path based on the system type
    if is_truenas:
        binary_path = input("Enter the binary path for Mellanox tools (or press Enter for default '/usr/bin'): ").strip() or "/usr/bin"
    else:
        binary_path = input("Enter the binary path for Mellanox tools (or press Enter for default '/opt/mellanox/bin'): ").strip() or "/opt/mellanox/bin"

    # Perform configuration
    try:
        system_requires_reboot = check_and_configure_mellanox_devices(binary_path, is_truenas)

        print("\nConfiguration completed successfully.")
    except Exception as e:
        print(f"An unexpected error occurred during configuration: {e}")


if __name__ == "__main__":
    main()