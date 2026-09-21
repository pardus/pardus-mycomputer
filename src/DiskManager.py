import subprocess
import os

import gi
gi.require_version("GioUnix", "2.0")
from gi.repository import GioUnix

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


def resolve_device(source):
    if source.startswith("UUID="):
        source = f"/dev/disk/by-uuid/{source[5:]}"
    elif source.startswith("LABEL="):
        source = f"/dev/disk/by-label/{source[6:]}"
    elif source.startswith("PARTUUID="):
        source = f"/dev/disk/by-partuuid/{source[9:]}"
    elif source.startswith("PARTLABEL="):
        source = f"/dev/disk/by-partlabel/{source[10:]}"

    return os.path.realpath(source)


def get_matching_fstab_sources(dev_path):
    target_real_path = resolve_device(dev_path)
    matching_sources = set()

    mount_points, _ = GioUnix.mount_points_get()

    for mount_point in mount_points:
        source = mount_point.get_device_path()

        if source and resolve_device(source) == target_real_path:
            matching_sources.add(source)

    return matching_sources


def is_drive_automounted(dev_path):
    try:
        return bool(get_matching_fstab_sources(dev_path))
    except OSError:
        return False


def set_automounted(dev_path, state):
    partition = os.path.basename(dev_path)
    mount_point = f"/mnt/{partition}"
    writer = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FstabWriter.py",)

    try:
        matching_sources = get_matching_fstab_sources(dev_path)

        if state:
            if matching_sources:
                return

            uuid = get_uuid_from_dev(dev_path)
            identifier = f"UUID={uuid}" if uuid else dev_path

            with open("/etc/fstab", "r") as f:
                fstab_content = f.read()

            fstab_content += f"{identifier} {mount_point} auto nosuid,nodev,nofail,x-gvfs-show 0 0\n"

        else:
            if not matching_sources:
                return

            with open("/etc/fstab", "r") as f:
                lines = []

                for line in f:
                    stripped = line.strip()

                    if not stripped or stripped.startswith("#"):
                        lines.append(line)
                        continue

                    parts = stripped.split()

                    if parts and parts[0] in matching_sources:
                        continue

                    lines.append(line)

            fstab_content = "".join(lines)

        subprocess.run(["/usr/bin/pkexec", writer], input=fstab_content, text=True, stdout=subprocess.DEVNULL, check=True)

    except (OSError, subprocess.CalledProcessError) as e:
        print(f"Error updating fstab: {e}")

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
