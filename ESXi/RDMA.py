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
            if "iser" in line and "true" in line.lower():  # 'true' indicates the module is loaded
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
            return None

        devices = []
        lines = result.stdout.strip().split("\n")
        for line in lines[2:]:  # Skip the first two lines (header)
            parts = line.split()
            if len(parts) > 0:
                devices.append(parts[0])  # Assuming the device name is the first column
        return devices
    except subprocess.TimeoutExpired:
        print("The operation to list RDMA devices has timed out.")
        return None
    except Exception as e:
        print(f"An error occurred while listing RDMA devices: {e}")
        return None


def list_active_rdma_adapters():
    """
    Lists all active RDMA adapters currently configured on the system.
    """
    print("Listing all active RDMA adapters...")
    command = ["esxcli", "rdma", "device", "list"]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if result.returncode != 0:
            error_message = result.stderr.strip()
            print(f"Failed to list active RDMA adapters. Error: {error_message}")
            return False

        lines = result.stdout.strip().split("\n")
        if len(lines) > 2:  # Skip the first two lines if there is data
            print("\nActive RDMA Adapters:")
            for line in lines:
                print(line)
        else:
            print("No active RDMA adapters found.")
        return True
    except subprocess.TimeoutExpired:
        print("The operation to list active RDMA adapters has timed out.")
        return False
    except Exception as e:
        print(f"An error occurred while listing active RDMA adapters: {e}")
        return False


def choose_rdma_device(devices):
    """
    Allows the user to select an RDMA device from the list or cancel the selection.
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
                return None  # Return None to indicate cancellation
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
            else:
                print("Invalid choice. Please select a valid number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


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


def main_menu():
    """
    Displays the main menu and handles user choices.
    """
    while True:
        print("\nMain Menu:")
        print("1. Enable RDMA/iSER for a device")
        print("2. Disable RDMA/iSER for a device")
        print("3. List Active RDMA Adapters")
        print("4. Exit to Main Menu")
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "4":
            print("Exiting. Goodbye!")
            sys.exit(0)  # Exit the program
        elif choice == "3":
            list_active_rdma_adapters()
        elif choice in ["1", "2"]:
            execute_device_action(choice)
        else:
            print("Invalid choice. Please select a valid option.")


def execute_device_action(action):
    """
    Handles enabling or disabling RDMA/iSER based on the user's choice.
    """
    devices = list_rdma_devices()
    if not devices:
        print("No RDMA devices found.")
        return

    selected_device = choose_rdma_device(devices)
    if selected_device is None:  # Cancel action
        print("Returning to main menu...")
        return

    if action == "1":
        success = enable_rdma_iser_local(selected_device)
    elif action == "2":
        success = disable_rdma_iser_local(selected_device)
    else:
        print("Invalid action.")
        return

    if success:
        print("Operation completed successfully.")
    else:
        print("Operation failed.")


if __name__ == "__main__":
    main_menu()