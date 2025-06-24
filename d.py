from scapy.all import ARP, Ether, srp
import socket
from mac_vendor_lookup import MacLookup

def scan_network_arp_only(ip_range):
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]
    devices = []

    for sent, received in result:
        ip = received.psrc
        mac = received.hwsrc
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            hostname = "Unbekannt"
        devices.append({
            "ip": ip,
            "mac": mac,
            "hostname": hostname
        })
    return devices

def kategorisiere_geraet(mac, hostname):
    mac_lookup = MacLookup()
    try:
        hersteller = mac_lookup.lookup(mac)
    except:
        hersteller = "Unbekannt"

    hersteller_lc = hersteller.lower()
    hostname_lc = hostname.lower()

    if "raspberry" in hostname_lc or "raspberry pi" in hersteller_lc:
        return "Raspberry Pi"
    elif "apple" in hersteller_lc:
        if "ipad" in hostname_lc:
            return "iPad"
        elif "iphone" in hostname_lc:
            return "iPhone"
        else:
            return "Apple Gerät"
    elif any(k in hersteller_lc for k in ["samsung", "huawei", "xiaomi", "oneplus"]):
        return "Handy"
    elif any(k in hostname_lc for k in ["pc", "win", "desktop", "laptop"]):
        return "PC"
    elif any(k in hersteller_lc for k in ["avm", "tp-link", "netgear", "router", "fritz"]):
        return "Router"
    else:
        return "Unbekannt"

def drucke_geraete(devices):
    print("\n📡 Gefundene Geräte im Netzwerk:")
    for d in devices:
        typ = kategorisiere_geraet(d["mac"], d["hostname"])
        print(f"{typ:15} | IP: {d['ip']:15} | MAC: {d['mac']:17} | Hostname: {d['hostname']}")

if __name__ == "__main__":
    ip_range = "10.29.0.0/22"
    print("🔍 Scanne das Netzwerk per ARP-Request...")
    devices = scan_network_arp_only(ip_range)
    drucke_geraete(devices)
