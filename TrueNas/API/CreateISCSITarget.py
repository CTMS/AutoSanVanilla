#!/usr/bin/python3

import requests
import json

# Configuration
# Create an api key at https://<trunas-ip>/ui/apikeys
TRUENAS_HOST = "https://<truenas-ip>"  # Replace with your TrueNAS Scale IP or hostname
API_KEY = "<your-api-key>"  # Replace with your TrueNAS Scale API key

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


def create_extent(name, zvol_path, rpm, disable_pblock):
    """
    Create an iSCSI extent for the given ZVOL with user-defined RPM and optional disabling of physical block size reporting.
    """
    url = f"{TRUENAS_HOST}/api/v2.0/iscsi/extent/"
    data = {
        "name": name,
        "type": "DISK",
        "disk": zvol_path,
        "blocksize": 512,  # Default block size; can be adjusted as needed
        "naa": None,
        "rpm": rpm,  # User-defined RPM
        "pblocksize": not disable_pblock,  # True = Enable physical block size, False = Disable
    }

    try:
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
    except Exception as e:
        print("Error during extent creation:", e)
        return None

    if response.status_code == 200:
        print(f"Extent '{name}' created successfully.")
        return response.json()
    else:
        print(f"Failed to create extent. {response.status_code}: {response.text}")
        return None


def create_target(name):
    """Create an iSCSI target."""
    url = f"{TRUENAS_HOST}/api/v2.0/iscsi/target/"
    data = {
        "name": name,
    }

    try:
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
    except Exception as e:
        print("Error during target creation:", e)
        return None

    if response.status_code == 200:
        print(f"Target '{name}' created successfully.")
        return response.json()
    else:
        print(f"Failed to create target. {response.status_code}: {response.text}")
        return None


def associate_extent_to_target(target_id, extent_id, lun_id):
    """Associate an extent to a target using a specific LUN ID."""
    url = f"{TRUENAS_HOST}/api/v2.0/iscsi/targetextent/"
    data = {
        "target": target_id,
        "extent": extent_id,
        "lunid": lun_id,
    }

    try:
        response = requests.post(url, headers=HEADERS, json=data, verify=False)
    except Exception as e:
        print("Error during extent-to-target association:", e)
        return

    if response.status_code == 200:
        print(f"Extent ID {extent_id} associated with Target ID {target_id} at LUN {lun_id}.")
    else:
        print(f"Failed to associate extent. {response.status_code}: {response.text}")


def get_user_input_for_extent(name):
    """Get user input for RPM and physical block size reporting for an extent."""
    # Ask for RPM value
    valid_rpm_values = ["SSD", "5400", "7200", "10000", "15000"]
    while True:
        rpm = input(f"Enter RPM for extent '{name}' (valid values: SSD, 5400, 7200, 10000, 15000): ").strip()
        if rpm in valid_rpm_values:
            break
        print("Invalid RPM value. Please try again.")

    # Ask if physical block size reporting should be disabled
    disable_pblock = input(f"Disable physical block size reporting for extent '{name}'? (yes/no): ").strip().lower() == "yes"

    return rpm, disable_pblock


def main():
    # Suppress SSL warnings if using self-signed certificates.
    requests.packages.urllib3.disable_warnings()

    print("Creating iSCSI configuration for LUNs...")

    # Get user inputs for both extents
    rpm1, disable_pblock1 = get_user_input_for_extent("lun16k_extent")
    rpm2, disable_pblock2 = get_user_input_for_extent("lun128k_extent")

    # 1. Create extents for the ZVOLs with user-defined options
    extent1 = create_extent("lun16k_extent", "zvol/dpool/lun16k", rpm1, disable_pblock1)
    extent2 = create_extent("lun128k_extent", "zvol/dpool/lun128k", rpm2, disable_pblock2)

    if not extent1 or not extent2:
        print("Failed to create one or more extents. Exiting.")
        return

    # 2. Create an iSCSI target named "san_dpool"
    target = create_target("san_dpool")
    if not target:
        print("Failed to create target. Exiting.")
        return

    # 3. Associate extents to target with LUN IDs 16 and 128
    target_id = target["id"]
    associate_extent_to_target(target_id, extent1["id"], 16)  # LUN ID 16
    associate_extent_to_target(target_id, extent2["id"], 128)  # LUN ID 128

    print("iSCSI configuration completed successfully.")


if __name__ == "__main__":
    main()