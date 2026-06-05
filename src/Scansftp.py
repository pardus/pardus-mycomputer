from scapy.all import ARP, Ether, srp
import netifaces
import ipaddress

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



def arp_scan(network):
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast Ethernet frame
    arp = ARP(pdst=network)  # ARP package

    packet = ether / arp

    result = srp(packet, timeout=2, verbose=0)[0]  # send package

    devices = []

    for sent, received in result:
        devices.append({"ip": received.psrc})

    return devices

#network = get_local_network()
#print(network)
#print(arp_scan(network))

