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

- **Testing IB connections**:
```script
# This test, 128 queue's with an mtu at 4096 and a sending size of around 64k
# Guid for this adaper was -g 1 (RoCev2).  do ibv_devinfo -v to use the correct GUID
# Client side:
ibv_rc_pingpong -g 1 -m 4096 -s 64000 -r 128 -n 1000000 <ip>

# Server side:
ibv_rc_pingpong -g 1 -m 4096 -s 64000 -r 128 -n 1000000
```

- **Restart targetcli-fb**:
```
systemctl restart rtslib-fb-targetctl.service
```


### **ISCSI Target Lun and Disk Settings**

#### You'll want to try to match (or close to a multiple that works for your load) block sizes, physical sectors, logical sectors and queue_sizes for your disks, all the way to the VM host OS.  
If these values are not matched or not close to multiples: block sizes, queues, etc..., `I/O penalties can occur.`  

- **Determine Disks Size on the SAN**:
```bash

lsblk -o NAME,MODEL,PHY-SEC,LOG-SEC,MIN-IO,OPT-IO,RQ-SIZE

NAME        MODEL                   PHY-SEC LOG-SEC MIN-IO   OPT-IO RQ-SIZE
sda         H0H72121CLAR12T0           4096    4096   4096        0     256
└─sda1                                 4096    4096   4096        0     256
sdb         H0H72121CLAR12T0           4096    4096   4096        0     256
└─sdb1                                 4096    4096   4096        0     256
sdc         H0H72121CLAR12T0           4096    4096   4096        0     256
└─sdc1                                 4096    4096   4096        0     256
sdd         H0H72121CLAR12T0           4096    4096   4096        0     256
└─sdd1                                 4096    4096   4096        0     256
sde         H0H72121CLAR12T0           4096    4096   4096        0     256
sdf         Samsung SSD 870 QVO 1TB     512     512    512        0      64
├─sdf1                                  512     512    512        0      64
├─sdf2                                  512     512    512        0      64
└─sdf3                                  512     512    512        0      64
sdg         H0H72121CLAR12T0           4096    4096   4096        0     256
└─sdg1                                 4096    4096   4096        0     256
sdh         H0H72121CLAR12T0           4096    4096   4096        0     256
sdi         H0H72121CLAR12T0           4096    4096   4096        0     256
└─sdi1                                 4096    4096   4096        0     256
sdj         H0H72121CLAR12T0           4096    4096   4096        0     256

```

- **Next step**:
```
# 254 is done on purpose for a buffer on the i/o
echo "options zfs zvol_blk_mq_queue_depth=254 zvol_blk_mq_blocks_per_thread=16 zvol_use_blk_mq=1" > /etc/modprobe.d/zfs.conf
# Limit ARC so it doesn't over run your system memory.  Give the system 60-70% breathing room
# In this case 192GB of 256GB's
echo "options zfs zfs_arc_max=206158430208" >> /etc/modprobe.d/zfs.conf

echo "options ib_core recv_queue_size=4096 send_queue_size=4096" > /etc/modprobe.d/ib_core.conf
echo "options ib_isert sg_tablesize=4096" > /etc/modprobe.d/ib_isert.conf
echo "options ib_iser pi_enable=1 max_sectors=4096" > /etc/modprobe.d/ib_iser.conf

# the kernel is going to need us to reserve more memory for how much data that can be processed now
echo "vm.min_free_kbytes=524288" >> /etc/sysctl.conf
echo "net.core.rmem_default=262144" >> /etc/sysctl.conf
echo "net.core.rmem_max=2097152" >> /etc/sysctl.conf
echo "net.core.wmem_default=262144" >> /etc/sysctl.conf
echo "net.core.wmem_max=2097152" >> /etc/sysctl.conf


# Update Kernel
update-initramfs -u
```

| Backend Type | `max_unmap_block_desc_count` | `max_unmap_lba_count` |
| --- | --- | --- |
| Thin-Provisioned HDD | 64 | 2097152 (1 GiB @ 512-byte) |
| SSD / NVMe | 256-1024 | 8388608 (4 GiB @ 512-byte) |
| Enterprise SAN | 256-1024 | 8388608 (4 GiB @ 512-byte) |
| High-Performance Use | 1024 or more | ~16 GiB (depends on system) |

### **VMWare**

| Attribute Name | Value (512-Byte Blocks) | Value (4096-Byte Blocks) | Notes |
| --- | --- | --- | --- |
| **`unmap_granularity`** | 2048 | 256 | Corresponds to 1 MiB granularity. |
| **`unmap_granularity_alignment`** | 2048 | 256 | Matches `unmap_granularity` for proper alignment. |
| **`unmap_zeroes_data`** | 0 | 0 | Prevents performance penalties by avoiding unnecessary zeroing operations. |


Most zfs setups will use 32Mib for I/O Optimization for ```max_unmap_lba_count```:
- For **32 MB**: `65,536 × 2 = 131,072 sectors`.
- For **64 MB**: `65,536 × 2 = 131,072 sectors`.
- For **128 MB**: `65,536 × 4 = 262,144 sectors`.
- For **256 MB**: `65,536 × 8 = 524,288 sectors`.
- For **512 MB**: `65,536 × 16 = 1,048,576 sectors`.


### **Drive Type, Block Size and Environment**

| **Environment** | **Block Size (Bytes)** | **Recommended `max_write_same_len`** | **Explanation** |
| --- | --- | --- | --- |
| **Thin-Provisioned HDD** | 512 | 131072 (64 MiB) | Moderate value optimized for thin provisioning without overwhelming traditional HDDs. |
|  | 4096 | 16384 (64 MiB) |  |
| **SSD / Enterprise SATA** | 512 | 262144 (128 MiB) | SSDs handle larger transfer sizes effectively; setting higher values can improve bulk data operations. |
|  | 4096 | 32768 (128 MiB) |  |
| **NVMe** | 512 | 1048576 (512 MiB) | NVMe storage has extremely high IOPS and throughput; large transfer sizes maximize its potential. |
|  | 4096 | 131072 (512 MiB) |  |
| **VMware Workloads** | 512 | 2097152 (1 GiB) | VMware ESXi benefits greatly from large `WRITE SAME` operations for space-efficient tasks like zeroing. |
|  | 4096 | 262144 (1 GiB) |  |
| **High-Performance Systems** | 512 | 8388608 (4 GiB) | For large-scale, high-performance systems where bulk transfers are critical. |
|  | 4096 | 1048576 (4 GiB) |  |


### **Queue Depth**

| **Environment** | **Storage Type** | **Recommended `queue_depth`** | **Explanation** |
| --- | --- | --- | --- |
| **Traditional HDD** | Single HDD (e.g., SATA) | 16–32 | HDDs can’t handle high parallelism; lower values prevent excessive queuing and lower latency. |
|  | RAID-backed HDD | 32–64 | With RAID, I/O parallelism slightly improves, so a moderate queue depth is better. |
| **SSD / SATA SSD** | Single SATA SSD | 64–128 | SATA SSDs handle multiple outstanding I/O, but queuing too much can increase latency. |
|  | RAID Array of SSDs | 128–256 | RAID arrays benefit from higher IOPS due to parallel SSDs. |
| **NVMe SSD** | NVMe drives | 256–1024+ | NVMe drives have extremely high queues (native queue depth: 64k), so high values improve throughput. |
| **Thin-Provisioned Storage** | Thin-Provisioned LUNs | 64–128 | Moderately high queue depths work best for space reclamation operations like VMware UNMAP. |
| **VMware Environments** | SSD-backed LUNs | 64–256 | VMware recommends medium to high queue depths for SSD-backed VMFS/vSAN datastores. |
|  | NVMe-backed LUNs | 256–1024 | VMware supports higher queue depths for NVMe due to its high IOPS nature. |
| **iSER (iSCSI over RDMA)** | RDMA-backed storage target | 256–1024+ | iSER supports high concurrency and very low latency, so higher queue depths maximize performance. |


### **Segment Lengths**
| **NIC/Network Type** | **Recommended MaxRecvDataSegmentLength** | **Recommended MaxXmitDataSegmentLength** | **Explanation** |
| --- | --- | --- | --- |
| **1 GbE iSCSI** | **128 KiB (131072)** | **128 KiB (131072)** | A low-speed network does not benefit from large segment sizes due to packet fragmentation. |
| **10 GbE iSCSI** | **256 KiB (262144)** | **256 KiB (262144)** | 10 GbE can handle larger transfers efficiently with minimal latency, making 256 KiB ideal. |
| **25 GbE iSCSI or iSER** | **512 KiB (524288)** | **512 KiB (524288)** | High-speed networks benefit from larger segments that reduce the number of PDUs per transfer. |
| **iSER (RDMA)** | **1 MiB (1048576)** | **1 MiB (1048576)** | RDMA can handle larger single operations due to its low-latency and zero-copy architecture. |
| **NVMe-oF Backends** | **1–4 MiB** | **1–4 MiB** | For NVMe-oF via iSCSI, use larger segment lengths to reduce overhead during high IOPS workloads. |
| **Legacy/extremely slow devices** | **64 KiB (65536)** | **64 KiB (65536)** | For very low-speed environments, small segment sizes help prevent memory overcommitment and retries. |



### **Here's some other settings that are good for thin and thick provisioning**:
`emulate_tpu` 1

`emulate_tpws` 1

### **ESXi**:
#### **Setting Round Robin Multipath**:
- This changes the default `Round Robin` behavior from iops=1000 to latency.
```esxicli
esxcli storage nmp psp roundrobin deviceconfig set -d <device_id> -t latency -U true -S 32
```

## Known Issues
- Doesn't handle subprocesses from apt particularly well. (Keep hitting return or rerun option if stuck)

---

## License
Include license details here (if applicable).

---

Feel free to integrate or modify `Configure.py` into your workflows for enhanced automation.