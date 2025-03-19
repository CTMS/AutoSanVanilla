import subprocess
import json


def get_user_inputs():
    """
    Get user input for optimization parameters with validation against minimum and maximum allowed values.
    :return: A dictionary containing all validated user inputs for the optimization parameters.
    """
    limits = {
        "max_vfs": {"min": 1, "max": 16},
        "max_queues": {"min": 1, "max": 32},
        "RSS": {"min": 1, "max": 32},
        "DYN_RSS": {"min": 0, "max": 1},
        "DRSS": {"min": 1, "max": 32}
    }
    user_inputs = {}
    print("Welcome to ESXi Optimization Configuration!")
    print("You will be prompted for optimization parameters.")
    print("Leave fields empty to use the default maximum values.\n")
    for param, limit in limits.items():
        while True:
            user_input = input(f"Enter value for {param} (Min: {limit['min']}, Max: {limit['max']}) [default: {limit['max']}]: ").strip()
            if not user_input:
                user_inputs[param] = limit['max']
                break
            try:
                value = int(user_input)
                if limit["min"] <= value <= limit["max"]:
                    user_inputs[param] = value
                    break
                else:
                    print(f"Invalid input. Please enter a number between {limit['min']} and {limit['max']}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
    return user_inputs


def execute_command(command):
    """
    Execute a shell command and return the output using subprocess with a 15-second timeout.
    :param command: Command to be executed.
    :return: Output of the command execution or None if an error occurs.
    """
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=15)
        if result.returncode != 0:
            print(f"Command failed with return code {result.returncode}: {result.stderr.strip()}")
            return None
        return result.stdout.strip() if result.stdout else None
    except subprocess.TimeoutExpired:
        print(f"Error: Command '{command}' timed out after 15 seconds.")
        return None
    except Exception as e:
        print(f"Unexpected error executing command '{command}': {e}")
        return None


def execute_commands(commands, execute_command_fn):
    """
    Helper function to execute a list of commands using the provided command execution function.
    :param commands: List of shell commands to execute.
    :param execute_command_fn: Function that executes a command and returns its output.
    """
    for command in commands:
        print(f"Executing: {command}")
        output = execute_command_fn(command)
        if output:
            print(output)


def optimize_esxi():
    """
    Optimize ESXi host by loading required modules and applying performance settings.
    """
    print("Starting ESXi optimization...")
    user_inputs = get_user_inputs()
    required_modules = ["nmlx5_core", "nmlx5_rdma", "iser", "vrdma"]
    print("\nChecking and loading required kernel modules...")
    for module in required_modules:
        output = execute_command(f"esxcli system module list | grep -i {module}")
        if "true" not in output.lower():
            print(f"Loading {module} module...")
            execute_command(f"esxcli system module load -m {module}")
        else:
            print(f"{module} module is already loaded.")
    print("\nSetting parameters for nmlx5_core module...")
    execute_command((
        f'esxcli system module parameters set -m nmlx5_core '
        f'-p "max_vfs={user_inputs["max_vfs"]} '
        f'max_queues={user_inputs["max_queues"]} RSS={user_inputs["RSS"]} '
        f'DYN_RSS={user_inputs["DYN_RSS"]} DRSS={user_inputs["DRSS"]}"'
    ))
    print("\nVerifying nmlx5_core module parameters...")
    execute_command("esxcli system module parameters list -m nmlx5_core")
    print("\nIncreasing iSER Max Command Queue")
    execute_command("esxcli system module parameters set -m iser -p 'iser_LunQDepth=512'")


    iscsi_commands = [
        "esxcli system settings advanced set -o /ISCSI/SocketRcvBufLenKB -i 2048",
        "esxcli system settings advanced set -o /ISCSI/SocketSndBufLenKB -i 2048",
        "esxcli system settings advanced set -o /Disk/SchedQuantum -i 16",
        "esxcli system settings advanced set -o /Disk/SchedQControlSeqReqs -i 512",
        "esxcli system module parameters set -m iscsi_vmk -p 'iscsivmk_LunQDepth=512 iscsivmk_HostQDepth=512 iscsivmk_InitialR2T=1 iscsivmk_MaxChannels=4'"
    ]
    print("\nSetting iSCSI buffers and Queues...")
    execute_commands(iscsi_commands, execute_command)
    tcp_commands = [
        "esxcli system settings advanced set -o /Net/TcpipHeapMax -i 1024",
        "esxcli system settings advanced set -o /Net/TcpipHeapSize -i 128",
        "esxcli system settings advanced set -o /Net/TcpipRxDispatchQueues -i 4"
    ]
    print("\nSetting TCP/IP stack and receive queue configurations...")
    execute_commands(tcp_commands, execute_command)
    print("\nESXi optimization completed successfully!")


def load_discovery_options():
    """
    Load discovery addresses from the Options.json file.
    :return: A list of discovery addresses, or an empty list if file loading fails.
    """
    try:
        with open("Options.json", "r") as file:
            options = json.load(file)
            return options.get("ISCSI", {}).get("discovery", [])
    except FileNotFoundError:
        print("Options.json file not found!")
    except json.JSONDecodeError:
        print("Failed to parse Options.json! Please ensure the file is valid JSON.")
    return []


def add_dynamic_discovery():
    """
    Add a dynamic discovery address to an ISCSI/ISER adapter.
    """
    print("\nStarting dynamic discovery configuration for ISCSI/ISER adapters...")
    adapter_list = execute_command("esxcli iscsi adapter list")
    if not adapter_list:
        print("No adapters found or unable to retrieve the list of adapters.")
        return
    adapters = [line.split()[0] for line in adapter_list.split("\n") if line.strip()]
    if not adapters:
        print("\nNo ISCSI/ISER adapters found.")
        return
    print("\nAvailable Adapters:")
    for i, adapter in enumerate(adapters, start=1):
        print(f"{i}. {adapter}")
    print(f"{len(adapters) + 1}. Cancel")
    while True:
        try:
            choice = int(input("\nSelect an adapter by entering the number (or select 'Cancel' to go back): ").strip())
            if choice == len(adapters) + 1:
                print("\nOperation canceled. Returning to the main menu.")
                return
            if 1 <= choice <= len(adapters):
                selected_adapter = adapters[choice - 1]
                break
            else:
                print("Invalid selection. Please choose a valid option.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    discovery_addresses = load_discovery_options()
    if not discovery_addresses:
        print("\nNo discovery addresses found in the Options.json file.")
        return
    for address in discovery_addresses:
        response = input(f"\nDo you want to add discovery address '{address}' to adapter '{selected_adapter}'? (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            print(f"Adding discovery address '{address}' to adapter '{selected_adapter}'...")
            command = f"esxcli iscsi adapter discovery sendtarget add -a {address} -A {selected_adapter}"
            result = execute_command(command)
            if result is not None:
                print(f"Successfully added discovery address '{address}' to adapter '{selected_adapter}'.")
            else:
                print(f"Failed to add discovery address '{address}' to adapter '{selected_adapter}'.")
        elif response in ["no", "n"]:
            print(f"Skipping discovery address '{address}'.")
        else:
            print("Invalid response. Skipping this address.")
    print("\nDynamic discovery configuration completed!")


def show_main_menu():
    """
    Display the main menu with three options for ISCSI/ISER configuration.
    """
    while True:
        print("\n--- ISCSI/ISER Configuration Menu ---")
        print("1. Optimize ISCSI/ISER and MLX Settings")
        print("2. Load Dynamic Discovery to ISCSI/ISER Adapters")
        print("3. Exit to Main Menu")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == "1":
            print("\nYou selected: Optimize ISCSI/ISER and MLX Settings")
            optimize_esxi()
        elif choice == "2":
            print("\nYou selected: Load Dynamic Discovery to ISCSI/ISER Adapters")
            add_dynamic_discovery()
        elif choice == "3":
            print("\nExiting to Main Menu... Goodbye!")
            break
        else:
            print("\nInvalid choice. Please select a valid option (1-3).")


# Start the menu
show_main_menu()