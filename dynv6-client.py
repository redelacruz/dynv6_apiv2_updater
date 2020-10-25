import click
import netifaces
import requests
import ipaddress

@click.command()
@click.argument('hostname')
@click.option('--token', prompt=True, hide_input=True)
@click.option('--interface', default='eth0')
def main(hostname, token, interface):
    addresses = netifaces.ifaddresses(interface)
    ipv6 = addresses[netifaces.AF_INET6]    
    for ip in ipv6:
        try:
            ip = ipaddress.IPv6Address(ip["addr"])
            if ip.is_global:
                ipv6 = str(ip)
        except ipaddress.AddressValueError:
            pass

    zone_id, host_id, record_ip = get_zone_host_id(token, hostname)
    #only update if there is a new IPv6 
    if ipaddress.IPv6Address(record_ip) != ipaddress.IPv6Address(ipv6) and zone_id and host_id:
        url = "https://dynv6.com/api/v2/zones/{0}/records/{1}".format(zone_id, host_id)
        payload = {"type":"AAAA","name":hostname.split(".")[0],"data":ipv6,"id":host_id,"zoneID":zone_id}
        header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
        r = requests.patch(url, data=payload, headers=header)
        if r.status_code == 200:
            print("Record for {} changed to {}".format(hostname, ipv6))
    else:
        print("Nothing todo. IPv6 unchanged!")

def get_zone_host_id(token, hostname):
    zones = ""
    host_id = ""
    zone_id = ""
    header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
    response = requests.get("https://dynv6.com/api/v2/zones", headers=header)
    if response.status_code == 200:
        zones = response.json()
        for zone in zones:
            zonename = ".".join(hostname.split(".")[1:])
            hostname = hostname.split(".")[0]
            if zone["name"] == zonename:
                id = zone["id"]
                url = "https://dynv6.com/api/v2/zones/{}/records".format(id)
                response = requests.get(url, headers=header)
                if response.status_code == 200:
                    records = response.json()
                    for record in records:
                        if record["name"] == hostname:
                            host_id = record["id"]
                            record_ip = record["data"]
                            zone_id = id
    return zone_id, host_id, record_ip

if __name__ == '__main__':
    main()