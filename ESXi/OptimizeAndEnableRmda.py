#!/bin/python3
import os
import time
import socket

# Check if paramiko is available
try:
    import paramiko
    paramiko_available = True
except ImportError:
    paramiko_available = False


def configure_esxi(esxi_host, username, password=None):
    """
    Configures ESXi to load kernel modules (nmlx5_core, nmlx5_rdma, iser, vrdma),
    and applies iSCSI, TCP stack, and module-specific parameter tuning. If reboot
    is chosen, it optionally waits for the host to come online and configures
    iSER adapters using available RDMA devices.

    Args:
        esxi_host (str): The IP or hostname of the ESXi host.
        username (str): Username for ESXi host login. Ignored if host is localhost.
        password (str): Password for ESXi host login (optional if using SSH key).
    """
    if not paramiko_available and esxi_host.lower() not in ["localhost", "127.0.0.1"]:
        print("\nERROR: The 'paramiko' module is not installed.")
        print("This script must be run locally on the ESXi host because SSH support is unavailable.")
        return

    try:
        # Determine if we're running locally
        is_local = esxi_host.lower() in ["localhost", "127.0.0.1"]

        # Function to execute commands (locally or remotely)
        def execute_command(command):
            if is_local:
                print(f"Running locally: {command}")
                stream = os.popen(command)
                output = stream.read()
                print(output)
                return output
            else:
                stdin, stdout, stderr = ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                if error:
                    print(f"Error: {error}")
                print(output)
                return output

        # If not localhost, create SSH client
        if not is_local:
            print(f"Connecting to {esxi_host} via SSH...")
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh_connect_args = {"hostname": esxi_host, "username": username}
            if password:
                ssh_connect_args["password"] = password

            ssh_client.connect(**ssh_connect_args)

        # Check and load modules
        def load_module(module_name):
            print(f"Checking if {module_name} module is loaded...")
            output = execute_command(f"esxcli system module list | grep {module_name}")
            if "true" not in output.lower():
                print(f"Loading {module_name} module...")
                execute_command(f"esxcli system module load -m {module_name}")
            else:
                print(f"{module_name} module is already loaded.")

        # Load all required modules
        required_modules = ["nmlx5_core", "nmlx5_rdma", "iser", "vrdma"]
        for module in required_modules:
            load_module(module)

        # Set `nmlx5_core` module parameters
        print("Setting parameters for nmlx5_core...")
        execute_command('esxcli system module parameters set -m nmlx5_core -p "max_vfs=16 max_queues=48 RSS=56 DYN_RSS=1 DRSS=48-56"')

        # Verify parameters for `nmlx5_core`
        print("Verifying nmlx5_core parameters...")
        execute_command("esxcli system module parameters list -m nmlx5_core")

        # Set iSCSI settings
        print("Setting iSCSI buffers...")
        commands = [
            "esxcli system settings advanced set -o /ISCSI/SocketRcvBufLenKB -i 4096",
            "esxcli system settings advanced set -o /ISCSI/SocketSndBufLenKB -i 4096"
        ]
        for cmd in commands:
            execute_command(cmd)

        # Set TCP/IP heap and receive queue settings
        print("Setting TCP/IP heap and receive dispatch queues...")
        commands = [
            "esxcli system settings advanced set -o /Net/TcpipHeapMax -i 1024",
            "esxcli system settings advanced set -o /Net/TcpipHeapSize -i 128",
            "esxcli system settings advanced set -o /Net/TcpipRxDispatchQueues -i 8"
        ]
        for cmd in commands:
            execute_command(cmd)

        # Final verification
        print("Verifying updated settings...")
        settings_to_verify = [
            "/ISCSI/SocketRcvBufLenKB",
            "/ISCSI/SocketSndBufLenKB",
            "/Net/TcpipHeapMax",
            "/Net/TcpipHeapSize",
            "/Net/TcpipRxDispatchQueues"
        ]
        for setting in settings_to_verify:
            print(f"Current value for {setting}:")
            execute_command(f"esxcli system settings advanced list -o {setting}")

        # Verify loaded modules
        print("Verifying loaded modules...")
        execute_command("esxcli system module list")

        # Ask if the host should be rebooted
        print("\nConfiguration complete! To apply some of these changes, a reboot may be required.")
        reboot = input("Would you like to reboot the host now? (yes/no): ").strip().lower()
        if reboot in ["yes", "y"]:
            print("Rebooting the ESXi host...")
            execute_command("reboot")

            # Ask if user wants to wait for the host to come back online
            wait_for_reboot = input("Would you like to wait for the host to come back online and create iSER adapters? (yes/no): ").strip().lower()
            if wait_for_reboot in ["yes", "y"]:
                print("Waiting for the host to come back online...")
                time.sleep(10)  # Initial sleep before checking

                # Poll the host to see when it comes back online
                while True:
                    try:
                        # Try to establish a connection to see if host is back online
                        if is_local:
                            print("Host seems to be back online (localhost detected).")
                            break
                        else:
                            test_socket = socket.create_connection((esxi_host, 22), timeout=5)
                            print("Host is back online!")
                            break
                    except (socket.timeout, socket.error):
                        print("Still waiting for the host to respond...")
                        time.sleep(10)

                # Reconnect via SSH if not running locally
                if not is_local:
                    print("Reconnecting to the host via SSH...")
                    ssh_client.connect(**ssh_connect_args)

                # Locate RDMA devices
                print("Locating RDMA devices...")
                rdma_devices_output = execute_command("esxcli rdma device list")
                print("RDMA Devices Found:")
                print(rdma_devices_output)

                # Parse and create iSER adapters for each RDMA device
                rdma_devices = [line.split()[0] for line in rdma_devices_output.splitlines() if line.strip()]
                for rdma_device in rdma_devices:
                    print(f"Creating iSER adapter for RDMA device: {rdma_device}")
                    execute_command(f"esxcli rdma iser add -d {rdma_device}")

        else:
            print("Reboot skipped. Please remember to manually reboot the ESXi host later to apply all settings.")

        # Close SSH connection (if not localhost)
        if not is_local:
            ssh_client.close()

    except Exception as e:
        print(f"An error occurred: {e}")


# === Usage Example ===
if __name__ == "__main__":
    # Prompt user for input
    print("ESXi Optimizer!  Because we're all lazy and machines will take over the world.")
    print("This setup is assuming at least 40Gb network cards, and a good amount of memory.")

    esxi_host = input("Enter the ESXi host IP or hostname (or 'localhost' if running locally): ").strip()
    username = None
    password = None

    # Only ask for username/password if not localhost
    if esxi_host.lower() not in ["localhost", "127.0.0.1"]:
        username = input("Enter the username (e.g., root): ").strip()
        password = input("Enter the password (leave blank if using an SSH key): ").strip() or None

    # Pass user inputs to the configure function
    configure_esxi(esxi_host, username, password)