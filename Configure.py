#!/bin/python3
import os
import sys
import time
import subprocess

# Import Paramiko if available
try:
    import paramiko
    paramiko_available = True
except ImportError:
    paramiko_available = False


def get_script_path():
    """
    Returns the directory path of this script.
    """
    return os.path.dirname(os.path.realpath(__file__))


def get_python_interpreter(connection_type, ssh_client=None):
    """
    Detect the Python interpreter to use on the remote host.
    Priority:
    1. Uses /tmp/ez_scripts/.env/venv/bin/python if it exists.
    2. Falls back to python3.
    """
    try:
        if connection_type == "local":
            return sys.executable
        print("Selecting interpreter...")
        stdin, stdout, stderr = ssh_client.exec_command("test -f /tmp/ez_scripts/.env/venv/bin/python && echo 'exists' || echo 'not_found'")
        result = stdout.read().decode().strip()
        if result == "exists":
            print(" - [/tmp/ez_scripts/.env/venv/bin/python]")
            return "/tmp/ez_scripts/.env/venv/bin/python"
        else:
            print(" - [python3]")
            return "python3"
    except Exception as e:
        print(f"Error detecting remote Python interpreter: {e}")
        return "python3"  # Default to system Python if detection fails


def is_host_online(host):
    """
    Check if the host is online by pinging it.
    """
    print(f"Pinging {host} to check if it is online...")
    try:
        ping_count = "-c" if os.name != "nt" else "-n"
        response = subprocess.run(["ping", ping_count, "1", host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return response.returncode == 0
    except Exception as e:
        print(f"Error while pinging {host}: {e}")
        return False


def connect_to_remote_host(host):
    """
    Connect to a remote host using SSH.
    Automatically uploads necessary files after a successful connection.
    """
    if not paramiko_available:
        print("Paramiko library is not available. Cannot connect to the remote host.")
        sys.exit(1)  # Exit if Paramiko is not available

    username = input(f"Enter the username for {host}: ").strip()
    password = input(f"Enter the password for {host}: ").strip()

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=host, username=username, password=password)
        print(f"Successfully connected to {host}.")
        print("\nUploading necessary files to the remote host...")
        upload_required_files_to_remote(ssh_client, get_script_path(), "/tmp/ez_scripts")
        print("Necessary files successfully uploaded!")
        return ssh_client
    except Exception as e:
        print(f"Failed to connect to {host}: {e}")
        sys.exit(1)  # Exit if the connection fails


def upload_required_files_to_remote(ssh_client, local_dir, remote_dir):
    """
    Upload only the necessary files to the remote host.
    """
    files = [
        "MLXDriverConfig/DriverConfig.py",
        "ESXi/Optimize.py",
        "ESXi/RDMA.py",
    ]

    try:
        sftp = ssh_client.open_sftp()
        # Create the remote directory if it does not exist
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass  # Directory already exists

        for file in files:
            local_path = os.path.join(local_dir, file)
            remote_path = os.path.join(remote_dir, os.path.basename(file))
            sftp.put(local_path, remote_path)
            print(f"Uploaded {local_path} to {remote_path}")
        sftp.close()
    except Exception as e:
        print(f"Failed to upload necessary files to the remote host: {e}")
        sys.exit(1)


def handle_interactive_session(stdin, stdout):
    """
    Handles input/output for interactive sessions.
    Provides input from the user for remote scripts requiring interaction.
    Returns the output of the interactive session.
    """
    output = ""  # Initialize output to capture all the remote responses
    try:
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                # Read and capture stdout from the remote command
                data = stdout.channel.recv(1024).decode()
                output += data
                print(data, end="")

                # If the remote script prompts for input, collect and send user input
                if data.strip().endswith((":", "?", ">")):
                    user_input = input().strip()
                    stdin.write(user_input + "\n")
                    stdin.flush()
        return output
    except KeyboardInterrupt:
        print("\nInteractive session interrupted by user.")
        raise
    except Exception as e:
        print(f"Error during interactive session: {e}")
        return output  # Return the output collected so far


def execute_remote_command(ssh_client, command, allow_input=True):
    """
    Execute a command on a remote host via SSH.
    If allow_input=True, handle interactive input/output between the remote shell and the user.
    """
    stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=allow_input)

    output = ""  # Initialize output to avoid undefined variable error
    try:
        if allow_input:
            output = handle_interactive_session(stdin, stdout)
        else:
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                print(f"Error during execution: {error}")
        return output.strip()
    except Exception as e:
        print(f"Error executing remote command: {e}")
        raise


def configure_driver(connection_type, ssh_client=None):
    """
    Configures the driver by invoking DriverConfig.py.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)

        if connection_type == "local":
            script = os.path.join(get_script_path(), "MLXDriverConfig", "DriverConfig.py")
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = "/tmp/ez_scripts/DriverConfig.py"
            command = f"{python_interpreter} {remote_script}"
            output = execute_remote_command(ssh_client, command, allow_input=True)
            print("\nDriver Configuration Output:")
            print(output)

        # Ask if the user wants to reboot after configuring the driver
        should_reboot = input("The driver configuration has completed. Would you like to reboot the system now? (yes/no): ").strip().lower()
        if should_reboot in ["yes", "y"]:
            reboot_host(connection_type, ssh_client)

    except Exception as e:
        print(f"Error during driver configuration: {e}")


def optimize_system(connection_type, ssh_client=None):
    """
    Optimize the system by running the Optimize.py script.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)

        if connection_type == "local":
            script = os.path.join(get_script_path(), "ESXi", "Optimize.py")
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = "/tmp/ez_scripts/Optimize.py"
            command = f"{python_interpreter} {remote_script}"
            output = execute_remote_command(ssh_client, command, allow_input=True)
            print("\nOptimization Output:")
            print(output)

        # Ask if the user wants to reboot after optimizing the system
        should_reboot = input("System optimization has completed. Would you like to reboot the system now? (yes/no): ").strip().lower()
        if should_reboot in ["yes", "y"]:
            reboot_host(connection_type, ssh_client)

    except Exception as e:
        print(f"Error during system optimization: {e}")


def configure_rdma_iser(connection_type, ssh_client=None):
    """
    Configure RDMA/iSER by running the RDMA.py script.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)

        if connection_type == "local":
            script = os.path.join(get_script_path(), "ESXi", "RDMA.py")
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = "/tmp/ez_scripts/RDMA.py"
            command = f"{python_interpreter} {remote_script}"
            output = execute_remote_command(ssh_client, command, allow_input=True)
            print("\nRDMA Configuration Output:")
            print(output)
    except Exception as e:
        print(f"Error during RDMA/iSER configuration: {e}")


def upload_all_scripts(connection_type, ssh_client):
    """
    Upload all necessary scripts to the remote host.
    """
    if connection_type == "local":
        print("This operation is only available for remote connections.")
    else:
        print("\nUploading all scripts to the remote host...")
        upload_required_files_to_remote(ssh_client, get_script_path(), "/tmp/ez_scripts")


def reboot_host(connection_type, ssh_client, host=None):
    """
    Reboot the remote or local host and optionally wait for it to come back online.
    """
    print("\nRebooting the host...")
    if connection_type == "local":
        os.system("sudo reboot")
    else:
        execute_remote_command(ssh_client, "reboot", allow_input=True)
        ssh_client.close()  # Close SSH connection as the host will reboot

    # Check if host is provided for remote connection
    if connection_type == "remote" and host:
        while True:
            user_choice = input("Would you like to wait until the host comes back online? (yes/no): ").strip().lower()
            if user_choice in ["yes", "y"]:
                print("Checking if the host is back online...")
                while not is_host_online(host):
                    print("Host is still offline, checking again in 10 seconds...")
                    time.sleep(10)  # Wait for 10 seconds before retrying
                print(f"The host {host} is now online!")
                break  # Exit the loop once the host is back online
            elif user_choice in ["no", "n"]:
                print("Not waiting for the host to come back online. Exiting.")
                break
            else:
                print("Invalid choice. Please enter 'yes' or 'no'.")


def show_menu():
    """
    Display the options menu to the user.
    """
    print("\nAvailable Operations:")
    print("1. Configure Drivers")
    print("2. Upload All Scripts to Remote Host")
    print("3. Optimize System")
    print("4. Configure RDMA/iSER")
    print("5. Reboot Host")
    print("6. Exit")


if __name__ == "__main__":
    print("EZ Configuration Tool! For ESXi and TrueNas. (Another Skeen Skript)")
    ssh_client = None  # Default to None

    connection_type = input("Will you configure the system locally or remotely? (local/remote): ").strip().lower()

    if connection_type == "remote":
        host = input("Enter the remote hostname or IP: ").strip()
        if not is_host_online(host):
            print(f"The host {host} is not reachable. Please check the connection and try again.")
            sys.exit(1)  # Exit if the host is offline

        ssh_client = connect_to_remote_host(host)  # Will exit if connection fails

    while True:
        show_menu()
        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            configure_driver(connection_type, ssh_client)
        elif choice == "2":
            upload_all_scripts(connection_type, ssh_client)
        elif choice == "3":
            optimize_system(connection_type, ssh_client)
        elif choice == "4":
            configure_rdma_iser(connection_type, ssh_client)
        elif choice == "5":
            reboot_host(connection_type, ssh_client)
        elif choice == "6":
            print("See ya later!")
            if ssh_client:
                ssh_client.close()
            sys.exit(0)
        else:
            print("Invalid option. Please select a valid choice.")