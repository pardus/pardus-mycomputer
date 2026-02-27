import subprocess


def get_file_info(file, network=False):
    values = None
    command = ["df", file, "--block-size=1000", "-T"]

    if network:
        try:
            process = subprocess.check_output(command, timeout=1)
        except subprocess.TimeoutExpired:
            print("timeout error on {}".format(file))
            return None
        except subprocess.CalledProcessError:
            print("CalledProcessError error on {}".format(file))
            return None
    else:
        try:
            process = subprocess.check_output(command)
        except Exception as e:
            print("get_file_info subprocess error: {}".format(file))
            return None

    lines = process.decode().splitlines()

    if len(lines) > 1:
        data = lines[1].split()
        if len(data) > 6:
            values = data[0], data[1], data[2], data[3], data[4], data[6]
        else:
            values = None

    if values is not None:
        keys = ["device", "fstype", "total_kb", "usage_kb", "free_kb", "mountpoint"]
        obj = dict(zip(keys, values))
        try:
            obj["usage_percent"] = (int(obj['total_kb']) - int(obj['free_kb'])) / int(obj['total_kb'])
        except:
            obj["usage_percent"] = 0
        try:
            obj["free_percent"] = int(obj['free_kb']) / int(obj['total_kb'])
        except:
            obj["free_percent"] = 0
    else:
        obj = {"device": "", "fstype": "", "total_kb": 0, "usage_kb": 0, "free_kb": 0, "mountpoint": "",
               "usage_percent": 0, "free_percent": 0}

    return obj


def get_uuid_from_dev(dev_path):
    result = subprocess.run(["lsblk", "-o", "PATH,UUID", "--raw"], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == dev_path:
            return parts[1]
    return ""


def is_drive_automounted(dev_path):
    uuid = get_uuid_from_dev(dev_path)
    try:
        with open("/etc/fstab", "r") as f:
            for line in f:
                if line.strip().startswith('#'):
                    continue
                if dev_path in line or (uuid and uuid in line):
                    return True
    except Exception:
        return False
    return False


def set_automounted(dev_path, value):
    if value and not is_drive_automounted(dev_path):
        partition = dev_path.split("/")[-1] # /dev/sda1 -> sda1
        fstab_string = f"{dev_path} /mnt/{partition} auto nosuid,nodev,nofail,x-gvfs-show 0 0\n"

        subprocess.run(["pkexec", "tee", "-a", "/etc/fstab"], input=fstab_string, text=True)

    elif not value and is_drive_automounted(dev_path):
        uuid = get_uuid_from_dev(dev_path)

        try:
            with open("/etc/fstab", "r") as f:
                lines = [l for l in f if dev_path not in l and (not uuid or uuid not in l)]
            tmpfile = "/tmp/fstab.tmp"
            with open(tmpfile, "w") as tf:
                tf.writelines(lines)
            subprocess.run(["pkexec", "mv", tmpfile, "/etc/fstab"])
        except Exception:
            pass


def get_filesystem_of_partition(partition_path):

    result = subprocess.run(["lsblk", "-o", "TYPE,PATH,FSTYPE", "-r"], capture_output=True, text=True)
    if result.returncode != 0:
        return "-"
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 3 and parts[1] == partition_path:
            return parts[2]

    return "-"

# import subprocess, threading
#
# class Command(object):
#     def __init__(self, cmd):
#         self.cmd = cmd
#         self.process = None
#         print(self.cmd)
#
#     def run(self, timeout):
#         def target():
#             print('Thread started')
#             self.process = subprocess.Popen(self.cmd, shell=True)
#             self.process.communicate()
#             print('Thread finished')
#
#         thread = threading.Thread(target=target)
#         thread.start()
#
#         thread.join(timeout)
#         if thread.is_alive():
#             print('Terminating process')
#             self.process.terminate()
#             thread.join()
#         print(self.process.returncode)

# command = Command("xdg-open {} &".format(path))
# command.run(timeout=1)
