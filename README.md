# AutoSanVanilla
A Skeen Python script that will optimize Mellenox Cards, vsphere, enable rdma, iser, and more



# AutoSanVanilla - Configure.py

`Configure.py` is a Python script that includes utilities to manage remote hosts, optimize configurations, and automate certain operations like file uploading and environment preparation. It is equipped with functionalities such as handling remote connections over SSH, detecting the appropriate Python interpreter to use, checking host availability, and uploading required files for further configurations. Utilities like interaction handling and network checks make it a versatile tool for system administrators and developers managing environments.

---

## Key Features of Configure.py
1. **Script Path Detection**:
    - Detects and returns the absolute directory path where the script is located.

2. **Python Interpreter Detection**:
    - Automatically detects the Python interpreter to use.
    - Prioritizes the custom virtual environment interpreter (`/tmp/ez_scripts/.env/venv/bin/python`) if available. Otherwise, falls back to Python 3.
    - Works both locally and on remote hosts.

3. **Host Availability Check**:
    - Pings the host to check if it is online.
    - Provides a reliable way to confirm network connectivity before running remote scripts.

4. **Remote Host Connection**:
    - Establishes an SSH connection to a remote host using `paramiko`.
    - Handles secure authentication for remote operations.

5. **File Upload**:
    - Uploads necessary configuration files to the remote host.
    - Ensures the correct directory structure is maintained on the remote host by creating the directory if it doesn't exist.

6. **Remote Execution**:
    - Designed to integrate remote script execution.
    - Can handle interactive command sessions on remote machines.

---

## File Structure

The `Configure.py` script is designed to work with a predefined directory structure. Below are the key components and files required by this script:

```
AutoSanVanilla/
│
├── Configure.py
├── MLXDriverConfig/
│   └── DriverConfig.py
├── ESXi/
│   ├── Optimize.py
│   ├── RDMA.py
│   TrueNas/ (in active development)
│   ├── CreateZvols.py
│   ├── CreateISER.py
|   VM
    ├── ResizeDisk.py

```

Ensure these files exist in the correct structure for `Configure.py` to successfully run operations like file uploads.

---

## Prerequisites
Before running `Configure.py`, ensure the following:
1. **Python 3 Installed**:
    - The script requires Python 3.x to run. You can check your Python version by running:
```shell script
python3 --version
```

2. **Required Python Libraries**:
    - If `paramiko` is not installed (needed for SSH functionality), install it using:
```shell script
pip install paramiko
```

3. **Network Configuration**:
    - Ensure that the host you want to connect to is reachable and SSH is enabled.

4. **Files Prepared**:
    - Files like `DriverConfig.py`, `Optimize.py`, and `RDMA.py` must be available in their respective directories for successful execution of file uploads.

5. **Note**:
    - After using TrueNas iser installation,  mellenox tools use `mstconfig` instead of the ESXi equivalent `mlxconfig` 
    - On TrueNas running `DriverConfig.py`:  It's a good idea to run the optimizations on both PCI busses that it detects.
---

## How to Use

### 1. Clone or Download the Script
First, ensure you have a local copy of the `AutoSanVanilla` project.

```shell script
git clone CTMS/AutoSanVanilla.git
cd AutoSanVanilla
```


---

### 2. Running the Script


Options:
use `Options.json` to configure discovery targets

```json
{
  "ISCSI": {
    "discovery": [
      "10.80.80.40:3260",
      "10.80.80.45:3260",
      "10.80.80.50:3260",
      "10.80.80.47:3260"
    ]
  }
}

```



Example:
```shell script
python3 Configure.py
EZ Configuration Tool! For ESXi and TrueNas. (Another Skeen Skript)
Will you configure the system locally or remotely? (local/remote): remote
Enter the remote hostname or IP: 10.15.1.152
Pinging 10.15.1.152 to check if it is online...
Enter the username for 10.15.1.152: root
Enter the password for 10.15.1.152: *****
Successfully connected to 10.15.1.152.

Uploading necessary files to the remote host...
Uploaded ./AutoSanVanilla/MLXDriverConfig/DriverConfig.py to /tmp/ez_scripts/DriverConfig.py
Uploaded ./AutoSanVanilla/ESXi/Optimize.py to /tmp/ez_scripts/Optimize.py
Uploaded ./AutoSanVanilla/ESXi/RDMA.py to /tmp/ez_scripts/RDMA.py
Necessary files successfully uploaded!

Available Operations:
1. Configure Drivers
2. Upload All Scripts to Remote Host
3. Optimize System
4. Configure RDMA/iSER
5. Reboot Host
6. Exit
Select an option (1-6): 

```
Example Running Choosing TrueNas:
```bashsupport pro shell
   Main Menu:
   1. Enable RDMA/iSER for a device
   2. Disable RDMA/iSER for a device
   3. List RDMA Devices
   4. Exit
   Enter your choice (1-4): 1
````
```bashsupport pro shell
   Available RDMA devices:
   1. vmhba40
   2. vmhba41
   0. Cancel
   Select a device (0-2): 1
   Enabling RDMA/iSER locally for device: vmhba40...
   Successfully enabled RDMA/iSER for device vmhba40.
   Configuring iSCSI parameters for adapter: vmhba40
   Set MaxRecvDataSegmentLength to 8192 for adapter vmhba40.
   Set MaxXmitDataSegmentLength to 8192 for adapter vmhba40.
```

```bashsupport pro script
--- ISCSI/ISER Configuration Menu ---
1. Optimize ISCSI/ISER and MLX Settings
2. Load Dynamic Discovery to ISCSI/ISER Adapters
3. Exit to Main Menu

Enter your choice (1-3): 2

Starting dynamic discovery configuration for ISCSI/ISER adapters...

Retrieving list of available adapters...

Available Adapters:
1. vmhba33
2. vmhba34
3. Cancel

Select an adapter by entering the number (or select 'Cancel' to go back): 1

Do you want to add discovery address '10.80.80.40:3260' to adapter 'vmhba33'? (yes/no): yes
Adding discovery address '10.80.80.40:3260' to adapter 'vmhba33'...
Successfully added discovery address '10.80.80.40:3260' to adapter 'vmhba33'.

Do you want to add discovery address '10.80.80.45:3260' to adapter 'vmhba33'? (yes/no): no
Skipping discovery address '10.80.80.45:3260'.

Do you want to add discovery address '10.80.80.50:3260' to adapter 'vmhba33'? (yes/no): yes
Adding discovery address '10.80.80.50:3260' to adapter 'vmhba33'...
Successfully added discovery address '10.80.80.50:3260' to adapter 'vmhba33'.
```

---
- **VM Operations**:
``` bash
   python3 VM/ResizeDisk.py
```
1. lists all partitions:
``` 
   NAME     SIZE FSTYPE  MOUNTPOINT
   sda       20G         
   sda1      1G  ext4    /
   sda2      19G         
```
2. You type the name of the partition you want to resize:
``` 
   Enter the partition name you want to resize (e.g., sda2): sda2
```
3. It asks whether the filesystem is **LVM** or **XFS**:
``` 
   Is the system using LVM or XFS? (type 'lvm' or 'xfs'): lvm
```
For `LVM`:
   - It asks for the logical volume path (e.g., `/dev/mapper/ubuntu--vg-ubuntu--lv`).
   - Uses `lvextend` and resizes the filesystem (`resize2fs` for ext4 or `xfs_growfs` for XFS).

For `XFS`:
   - It asks for the mount point (e.g., `/mnt`).
   - Runs `xfs_growfs` and `xfs_info`.

**Finally, it displays the updated disk state.**


---

## Troubleshooting

- **Paramiko Not Installed**:
  If you see an error about `paramiko` missing, install it using:
```shell script
pip install paramiko
```
- **SSH Connection Issues**:
    - Ensure the host is reachable and SSH is enabled.
    - Double-check the username, password, and network configurations.

- **File Not Found**:
  Ensure your project contains all files (`DriverConfig.py`, `Optimize.py`, etc.) in the required folder structure.

---

## Known Issues
- Doesn't handle subprocesses from apt particularly well. (Keep hitting return or rerun option if stuck)

---

## License
Include license details here (if applicable).

---

Feel free to integrate or modify `Configure.py` into your workflows for enhanced automation.