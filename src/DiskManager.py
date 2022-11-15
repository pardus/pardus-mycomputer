import os,subprocess

def get_file_info(file):
    process = subprocess.run(f"df '{file}' --block-size=1000 | awk 'NR==1 {{next}} {{print $1,$2,$3,$4,$6; exit}}'", shell=True, capture_output=True)

    keys = ["device", "total_kb", "usage_kb", "free_kb", "mountpoint"]
    obj = dict(zip(keys, process.stdout.decode("utf-8").strip().split(" ")))

    try:
        obj["usage_percent"] = (int(obj['total_kb']) - int(obj['free_kb'])) / int(obj['total_kb'])
    except:
        obj["usage_percent"] = 0
    try:
        obj["free_percent"] = int(obj['free_kb']) / int(obj['total_kb'])
    except:
        obj["free_percent"] = 0

    return obj

def get_uuid_from_dev(dev_path):
    process = subprocess.run(f"lsblk -o PATH,UUID | grep {dev_path}", shell=True, capture_output=True)

    if process.returncode != 0:
        return ""
    
    uuid = process.stdout.decode("utf-8").strip().split(" ")[1]
    return uuid

def is_drive_automounted(dev_path):
    uuid = get_uuid_from_dev(dev_path)
    
    process = subprocess.run(f'grep -E "{dev_path}|{uuid}" /etc/fstab | grep -v -E "#.*({dev_path}|{uuid})"', shell=True, capture_output=True)

    if process.returncode != 0:
        return False
    
    return True

def set_automounted(dev_path, value):
    if value and not is_drive_automounted(dev_path):
        partition = dev_path.split("/")[-1] # /dev/sda1 -> sda1
        fstab_string = f"{dev_path} /mnt/{partition} auto nosuid,nodev,nofail,x-gvfs-show 0 0"

        process = subprocess.run(f'echo "{fstab_string}" | pkexec tee -a /etc/fstab', shell=True)

    elif not value and is_drive_automounted(dev_path):
        partition = dev_path.split("/")[:-1] # /dev/sda1 -> sda1
        uuid = get_uuid_from_dev(dev_path)

        dev_path_backslashes = dev_path.replace("/","\/")
        cmd = f"pkexec sed -ri 's/.*({dev_path_backslashes}|{uuid}).*//g' /etc/fstab"
        process = subprocess.run(cmd, shell=True)
        
def get_filesystem_of_partition(partition_path):
    process = subprocess.run(f'lsblk -o TYPE,PATH,FSTYPE -r | grep " {partition_path} "', shell=True, capture_output=True)

    output = process.stdout.decode("utf-8").strip()
    if output == "":
        return "-"
    return output.split(" ")[2]

#print(is_drive_automounted("/dev/nvme0n1p3"))