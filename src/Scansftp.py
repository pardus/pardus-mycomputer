import subprocess
import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import paramiko
import netifaces

# a function that retrieves the network address of the connected interface
def get_local_network():
    # Find the interface used by the default gateway
    gateway_info = netifaces.gateways()
    interface = gateway_info['default'][netifaces.AF_INET][1]

    # Interface IP and netmask information
    addr_info = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]

    ip_addr = addr_info['addr']
    netmask = addr_info['netmask']

    # Create a network address
    network = ipaddress.IPv4Network(f"{ip_addr}/{netmask}", strict=False)

    return str(network)


def get_ip_neigh():
    ips = set()
    try:
        out = subprocess.check_output(["ip", "neigh"]).decode()
        for line in out.splitlines():
            parts = line.split()
            if len(parts) > 0:
                ip = parts[0]
                if ip.count(".") == 3:  # IPv4 basic filter
                    ips.add(ip)
    except Exception as e:
        print("ip neigh error:", e)

    return ips


def check_ssh_sftp(host, port=22, timeout=3):
    # Checking if the SSH port is open
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

    # Sending a fake credential results in an    AuthenticationException → This means SFTP exists
    transport = paramiko.Transport((host, port))
    transport.banner_timeout = timeout

    try:
        transport.connect(
            username='__probe__',
            password='__probe__'
        )
        return True

    except paramiko.AuthenticationException:
        return True   # an authentication error means the SFTP service is active

    except paramiko.SSHException:
        return False  # SSH handshake failed

    except Exception:
        return False

# scan devices
def scan_devices(network, max_threads=30, delay=0.02):
    net = ipaddress.ip_network(network, strict=False)
    results = []

    def worker(ip):
        ip = str(ip)
        if check_ssh_sftp(ip):  # this address is being checked to see if it is an SSH server
            return ip
        return None

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []

        for ip in net.hosts():
            futures.append(executor.submit(worker, ip))
            time.sleep(delay)

        for f in as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    print(results)
    return results


#netaddress = get_local_network()
#hosts = scan(netaddress)
#for h in hosts:
#    print(h)

