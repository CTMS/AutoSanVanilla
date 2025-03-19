import sys
import subprocess


def check_and_load_iser_module():
    """
    Checks if the 'iser' module is loaded and attempts to load it if not found.
    """
    print("Checking if 'iser' module is loaded...")
    command_check = ["esxcli", "system", "module", "list"]
    try:
        result = subprocess.run(command_check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if result.returncode != 0:
            print(f"Failed to check system modules. Error: {result.stderr.strip()}")
            return False

        # Check if the 'iser' module is present and loaded
        iser_loaded = False
        for line in result.stdout.strip().split("\n"):
            if "iser" in line and "true" in line.lower():
                iser_loaded = True
                break

        if not iser_loaded:
            print("'iser' module is not loaded.")
            load = input("Would you like to attempt to load the 'iser' module? (yes/no): ").strip().lower()
            if load in ["yes", "y"]:
                command_load = ["esxcli", "system", "module", "load", "-m", "iser"]
                load_result = subprocess.run(command_load, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if load_result.returncode == 0:
                    print("'iser' module successfully loaded.")
                    return True
                else:
                    print(f"Failed to load 'iser' module. Error: {load_result.stderr.strip()}")
                    return False
            else:
                print("Skipping 'iser' module loading.")
                return False
        else:
            print("'iser' module is already loaded.")
            return True

    except subprocess.TimeoutExpired:
        print("The operation to check/load 'iser' module has timed out.")
        return False
    except Exception as e:
        print(f"An error occurred while checking/loading 'iser' module: {e}")
        return False


def list_rdma_devices():
    """
    Lists all available RDMA devices on the system.
    """
    print("Fetching available RDMA devices...")
    command = ["esxcli", "rdma", "device", "list"]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if result.returncode != 0:
            error_message = result.stderr.strip()
            print(f"Failed to fetch RDMA devices. Error: {error_message}")
            return []

        devices = []
        lines = result.stdout.strip().split("\n")
        for line in lines[2:]:  # Skip the first two lines (header)
            parts = line.split()
            if len(parts) > 0:
                devices.append(parts[0])  # Assuming the device name is the first column
        return devices
    except subprocess.TimeoutExpired:
        print("The operation to list RDMA devices has timed out.")
        return []
    except Exception as e:
        print(f"An error occurred while listing RDMA devices: {e}")
        return []


def enable_rdma_iser_local(device):
    """
    Enables RDMA/iSER for a device locally on the system.
    """
    print(f"Enabling RDMA/iSER locally for device: {device}...")
    command = ["esxcli", "rdma", "iser", "add", "-d", device]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if result.returncode != 0:
            error_message = result.stderr.strip()
            print(f"Failed to enable RDMA/iSER for device {device}.\nError: {error_message}")
            return False
        print(f"Successfully enabled RDMA/iSER for device {device}.")
        print(
            "\n** Next Step Required **"
            "\nPlease log into the vSphere Client and bind the RDMA adapter to a VMkernel (VMK) interface."
            "\nThis step is necessary for the RDMA/iSER configuration to become active."
        )
        return True
    except subprocess.TimeoutExpired:
        print(f"The operation to enable RDMA/iSER for device {device} has timed out.")
        return False
    except Exception as e:
        print(f"An error occurred while enabling RDMA/iSER locally for device {device}: {e}")
        return False


def disable_rdma_iser_local(device):
    """
    Disables RDMA/iSER for a device locally on the system.
    """
    print(f"Disabling RDMA/iSER locally for device: {device}...")
    command = ["esxcli", "rdma", "iser", "delete", "-d", device]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if result.returncode != 0:
            error_message = result.stderr.strip()
            print(f"Failed to disable RDMA/iSER for device {device}.\nError: {error_message}")
            return False
        print(f"Successfully disabled RDMA/iSER for device {device}.")
        return True
    except subprocess.TimeoutExpired:
        print(f"The operation to disable RDMA/iSER for device {device} has timed out.")
        return False
    except Exception as e:
        print(f"An error occurred while disabling RDMA/iSER locally for device {device}: {e}")
        return False


def get_iscsi_adapters():
    """
    Retrieves the list of all iSCSI adapters on the system.

    Returns:
        list: A list of adapter names (e.g., ['vmhba32', 'vmhba33']).
    """
    try:
        command = ["esxcli", "iscsi", "adapter", "list"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        adapters = []

        # Extract adapter names from the output
        lines = result.stdout.strip().split("\n")
        for line in lines[2:]:  # Skip the header row
            parts = line.split()
            if len(parts) > 1 and parts[1] == "iser":
                adapters.append(parts[0])  # Assuming adapter name is the first column

        return adapters
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve iSCSI adapters. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return []

def set_iscsi_buffer_size(adapter_name, max_recv=1048576, max_xmit=1048576):
    """
    Configures iSCSI max receive and transmit buffer size for a specific adapter.

    Args:
        adapter_name (str): The name of the iSCSI adapter (e.g., 'vmhba32').
        max_recv (int): Maximum receive buffer size (in bytes).
        max_xmit (int): Maximum transmit buffer size (in bytes).
    """
    try:
        # Set MaxRecvDataSegmentLength
        recv_command = [
            "esxcli", "iscsi", "adapter", "param", "set",
            "-A", adapter_name, "-k", "MaxRecvDataSegment", "-v", str(max_recv)
        ]
        subprocess.run(recv_command, check=True, text=True)
        print(f"Set MaxRecvDataSegLen to {max_recv} for adapter {adapter_name}.")

        send_command = [
            "esxcli", "iscsi", "adapter", "param", "set",
            "-A", adapter_name, "-k", "MaxBurstLength", "-v", str(max_xmit)
        ]
        subprocess.run(send_command, check=True, text=True)

        first_command = [
            "esxcli", "iscsi", "adapter", "param", "set",
            "-A", adapter_name, "-k", "FirstBurstLength", "-v", str(max_xmit)
        ]
        subprocess.run(first_command, check=True, text=True)
        print(f"Set MaxBurstLength to {max_xmit} for adapter {adapter_name}.")
        print(f"Set FirstBurstLength to {max_xmit} for adapter {adapter_name}.")


    except subprocess.CalledProcessError as e:
        print(f"Failed to set iSCSI buffer sizes for adapter {adapter_name}. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def configure_all_iscsi_adapters(max_recv=1048576, max_xmit=1048576):
    """
    Configures iSCSI buffer sizes for all adapters fetched from the system.

    Args:
        max_recv (int): Maximum receive buffer size (in bytes).
    """
    adapters = get_iscsi_adapters()
    if not adapters:
        print("No iSCSI adapters found.")
        return

    print("Configuring iSCSI buffer sizes for all adapters...")
    for adapter in adapters:
        print(f"\nProcessing adapter: {adapter}")
        set_iscsi_buffer_size(adapter, max_recv, max_xmit)



def execute_device_action(action, devices):
    """
    Handles enabling or disabling RDMA/iSER for a selected device.
    """
    print("\nAvailable RDMA devices:")
    for idx, device in enumerate(devices, start=1):
        print(f"{idx}. {device}")
    print("0. Cancel")  # Add a cancel option

    while True:
        try:
            choice = int(input(f"Select a device (0-{len(devices)}): ").strip())
            if choice == 0:
                print("Operation cancelled by the user.")
                return  # Exit without action
            elif 1 <= choice <= len(devices):
                selected_device = devices[choice - 1]
                print(f"Selected device: {selected_device}")
                if action == "enable":
                    if enable_rdma_iser_local(selected_device):
                        print(f"Configuring iSCSI parameters for adapter: {selected_device}")
                        set_iscsi_buffer_size(selected_device)
                elif action == "disable":
                    disable_rdma_iser_local(selected_device)
                return
            else:
                print("Invalid choice. Please select a valid number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def main_menu():
    """
    Displays the main menu and handles user choices.
    """
    while True:
        print("\nMain Menu:")
        print("1. Enable RDMA/iSER for a device")
        print("2. Disable RDMA/iSER for a device")
        print("3. List RDMA Devices")
        print("4. Exit to Main Menu")
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "4":
            print("Exiting. Goodbye!")
            sys.exit(0)  # Exit the program
        elif choice == "3":
            devices = list_rdma_devices()
            if devices:
                print(f"Found RDMA devices: {', '.join(devices)}")
            else:
                print("No RDMA devices found.")
        elif choice in ["1", "2"]:
            devices = list_rdma_devices()
            if devices:
                action = "enable" if choice == "1" else "disable"
                execute_device_action(action, devices)
                if choice == "1":
                    configure_all_iscsi_adapters()
            else:
                print("No RDMA devices available.")
        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main_menu()