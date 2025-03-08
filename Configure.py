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
        stdin, stdout, stderr = ssh_client.exec_command(
            "test -f /tmp/ez_scripts/.env/venv/bin/python && echo 'exists' || echo 'not_found'"
        )
        result = stdout.read().decode().strip()
        return "/tmp/ez_scripts/.env/venv/bin/python" if result == "exists" else "python3"
    except Exception as e:
        print(f"Error detecting remote Python interpreter: {e}")
        return "python3"


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
        print("Paramiko library is not available. Exiting.")
        sys.exit(1)

    username = input(f"Enter the username for {host}: ").strip()
    password = input(f"Enter the password for {host}: ").strip()

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=host, username=username, password=password)
        print(f"Connected to {host}.")
        upload_required_files_to_remote(ssh_client, get_script_path(), "/tmp/ez_scripts")
        return ssh_client
    except Exception as e:
        print(f"Failed to connect to {host}: {e}")
        sys.exit(1)


def upload_required_files_to_remote(ssh_client, local_dir, remote_dir):
    """
    Upload necessary files to the remote host.
    """
    files = [
        "MLXDriverConfig/DriverConfig.py",
        "ESXi/Optimize.py",
        "ESXi/RDMA.py",
        "TrueNas/EnableISER.py",
        "TrueNas/CreateZvols.py",
    ]
    try:
        sftp = ssh_client.open_sftp()
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass  # Directory already exists

        for file in files:
            local_path = os.path.join(local_dir, file)
            remote_path = os.path.join(remote_dir, os.path.basename(file))
            sftp.put(local_path, remote_path)
            print(f"Uploaded: {local_path} -> {remote_path}")
        sftp.close()
    except Exception as e:
        print(f"Failed to upload files to remote: {e}")
        sys.exit(1)


def configure_driver(connection_type, ssh_client=None):
    """
    Configure drivers using DriverConfig.py.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)
        if connection_type == "local":
            script = os.path.join(get_script_path(), "MLXDriverConfig", "DriverConfig.py")
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = "/tmp/ez_scripts/DriverConfig.py"
            command = f"{python_interpreter} {remote_script}"
            execute_remote_command(ssh_client, command)
    except Exception as e:
        print(f"Error while configuring drivers: {e}")


def execute_truenas_script(connection_type, ssh_client, script_name):
    """
    Execute a TrueNAS script by name.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)
        if connection_type == "local":
            script = os.path.join(get_script_path(), "TrueNas", script_name)
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = f"/tmp/ez_scripts/{script_name}"
            command = f"{python_interpreter} {remote_script}"
            execute_remote_command(ssh_client, command)
    except Exception as e:
        print(f"Error executing TrueNAS script {script_name}: {e}")


def execute_remote_command(ssh_client, command):
    """
    Execute a command on the remote host.
    """
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(stdout.read().decode())
        error = stderr.read().decode()
        if error:
            print(f"Error: {error}")
    except Exception as e:
        print(f"Error executing remote command: {e}")


def show_menu():
    """
    Display the main menu.
    """
    print("\nMain Menu:")
    print("1. Upload All Scripts to Remote Host")
    print("2. Configure Drivers")
    print("3. ESXi")
    print("4. TrueNAS")
    print("5. Exit")


def esxi_menu(connection_type, ssh_client):
    """
    Show the ESXi menu.
    """
    while True:
        print("\nESXi Menu:")
        print("1. Optimize System")
        print("2. Configure RDMA/iSER")
        print("3. Back to Main Menu")
        choice = input("Select an option (1-3): ").strip()
        if choice == "1":
            optimize_system(connection_type, ssh_client)
        elif choice == "2":
            configure_rdma_iser(connection_type, ssh_client)
        elif choice == "3":
            break
        else:
            print("Invalid option. Please try again.")


def truenas_menu(connection_type, ssh_client):
    """
    Show the TrueNAS menu.
    """
    while True:
        print("\nTrueNAS Menu:")
        print("1. Enable ISER")
        print("2. Create Zvols")
        print("3. Back to Main Menu")
        choice = input("Select an option (1-3): ").strip()
        if choice == "1":
            execute_truenas_script(connection_type, ssh_client, "EnableISER.py")
        elif choice == "2":
            execute_truenas_script(connection_type, ssh_client, "CreateZvols.py")
        elif choice == "3":
            break
        else:
            print("Invalid option. Please try again.")


def optimize_system(connection_type, ssh_client=None):
    """
    Optimize the system by running Optimize.py.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)
        if connection_type == "local":
            script = os.path.join(get_script_path(), "ESXi", "Optimize.py")
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = "/tmp/ez_scripts/Optimize.py"
            command = f"{python_interpreter} {remote_script}"
            execute_remote_command(ssh_client, command)
    except Exception as e:
        print(f"Error optimizing system: {e}")


def configure_rdma_iser(connection_type, ssh_client=None):
    """
    Configure RDMA/iSER by running RDMA.py.
    """
    try:
        python_interpreter = get_python_interpreter(connection_type, ssh_client)
        if connection_type == "local":
            script = os.path.join(get_script_path(), "ESXi", "RDMA.py")
            subprocess.run([python_interpreter, script], check=True)
        else:
            remote_script = "/tmp/ez_scripts/RDMA.py"
            command = f"{python_interpreter} {remote_script}"
            execute_remote_command(ssh_client, command)
    except Exception as e:
        print(f"Error configuring RDMA/iSER: {e}")


if __name__ == "__main__":
    print("EZ Configuration Tool for ESXi and TrueNAS (Another Skeen Skript)")
    ssh_client = None

    connection_type = input("Configure locally or remotely? (local/remote): ").strip().lower()
    if connection_type == "remote":
        host = input("Enter remote host (IP/hostname): ").strip()
        if is_host_online(host):
            ssh_client = connect_to_remote_host(host)
        else:
            print(f"Host {host} is unreachable.")
            sys.exit(1)

    while True:
        show_menu()
        choice = input("Select an option (1-5): ").strip()
        if choice == "1":
            upload_required_files_to_remote(ssh_client, get_script_path(), "/tmp/ez_scripts") if ssh_client else print("Remote only.")
        elif choice == "2":
            configure_driver(connection_type, ssh_client)
        elif choice == "3":
            esxi_menu(connection_type, ssh_client)
        elif choice == "4":
            truenas_menu(connection_type, ssh_client)
        elif choice == "5":
            print("Exiting. Goodbye!")
            if ssh_client:
                ssh_client.close()
            sys.exit(0)
        else:
            print("Invalid option. Please try again.")