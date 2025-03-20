import json
import os
import ssl
from pyVim import connect
from pyVmomi import vim

# Path to Options.json
options_file = "Options.json"

# Required fields for vsphere.options
required_vsphere_fields = [
    "vcenter",
    "username",
    "password",
    "vm_name",
    "host_name"
]

# Load Options.json
if not os.path.exists(options_file):
    print(f"{options_file} not found!")
    exit(1)

with open(options_file, "r") as file:
    options = json.load(file)

# Validate that all required fields exist, prompt user for missing ones (without saving to file)
if "vsphere" not in options or "options" not in options["vsphere"]:
    print("Missing 'vsphere.options' in Options.json!")
    exit(1)

vsphere_options = options["vsphere"]["options"]
for field in required_vsphere_fields:
    if field not in vsphere_options:
        user_input = input(f"Enter value for '{field}': ")
        vsphere_options[field] = user_input  # Temporarily populate missing values

# Assign variables from Options.json or user input
vcenter = vsphere_options["vcenter"]
username = vsphere_options["username"]
password = vsphere_options["password"]
vm_name = vsphere_options["vm_name"]
host_name = vsphere_options["host_name"]

# Disable SSL warnings (for self-signed certificates)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_NONE

# Connect to vCenter Server
try:
    service_instance = connect.SmartConnect(host=vcenter, user=username, pwd=password, sslContext=context)
    content = service_instance.content
    print("Connected to vCenter Server!")
except Exception as e:
    print(f"Failed to connect to vCenter: {e}")
    exit(1)

# Locate the VM
vm = None
for child in content.rootFolder.childEntity:
    datacenter = child
    vm_folder = datacenter.vmFolder
    vm_list = vm_folder.childEntity
    for v in vm_list:
        if v.name == vm_name:
            vm = v
            break

if not vm:
    print(f"VM '{vm_name}' not found!")
    connect.Disconnect(service_instance)
    exit(1)

# Power off the VM
if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
    print(f"Powering off VM: {vm_name}")
    task = vm.PowerOffVM_Task()
    task_result = task.info.state
    if task_result == "success":
        print("VM Powered Off")
    else:
        print(f"Failed to power off the VM: {task_result}")

# Remove PCI passthrough device
print("Removing PCI passthrough devices...")
pci_device = None
for device in vm.config.hardware.device:
    if isinstance(device, vim.vm.device.VirtualPCIController):
        pci_device = device
        break

if pci_device:
    device_spec = vim.vm.device.VirtualDeviceSpec()
    device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    device_spec.device = pci_device

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [device_spec]

    task = vm.ReconfigVM_Task(spec=spec)
    print("PCI passthrough device removed.")

# Perform migration (if needed)
host = None
host_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], recursive=True).view
for h in host_list:
    if h.name == host_name:
        host = h
        break

if host:
    print(f"Migrating VM to host: {host_name}")
    relocate_spec = vim.vm.RelocateSpec(host=host)
    task = vm.RelocateVM_Task(spec=relocate_spec)
    print("Migration completed.")
else:
    print(f"Host '{host_name}' not found! Skipping migration.")

# Add the PCI passthrough device back
if pci_device:
    print("Re-adding PCI passthrough device...")
    device_spec = vim.vm.device.VirtualDeviceSpec()
    device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    device_spec.device = pci_device

    spec = vim.vm.ConfigSpec()
    spec.deviceChange = [device_spec]
    task = vm.ReconfigVM_Task(spec=spec)
    print("PCI passthrough device re-added.")

# Power on the VM
print("Powering on VM...")
task = vm.PowerOnVM_Task()
print("VM Powered On")

# Disconnect from vCenter
connect.Disconnect(service_instance)
print("Disconnected from vCenter Server.")