from scapy.all import ARP, Ether, srp
import netifaces
import ipaddress
import paramiko
import socket

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


def scan_devices(network):
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast Ethernet frame
    arp = ARP(pdst=network)  # ARP package

    packet = ether / arp

    result = srp(packet, timeout=2, verbose=0)[0]  # send package

    devices = []

    for sent, received in result:
        devices.append({"ip": received.psrc})

    return devices


def is_sftp_server(host, port=22, timeout=3):
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

#netaddress = get_local_network()
#devices = scan_devices(netaddress)
#for d in devices:
#    if is_sftp_server(d['ip']):
#        print(f"{d} -- SFTP VAR")
#    else:
#        print(f"{d} -- SFTP YOK")

