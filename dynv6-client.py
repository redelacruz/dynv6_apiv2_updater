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
    
    # get current zone addresses
    zonename, zone_id, name, host_id, record_ipv6 = get_zone_host_data(token, hostname)
    if not zone_id:
        print("Zone does not exist. Check the zone and try again.")
        return
    if not host_id:
        print("Host does not exist in {}. Check the host and try again.".format(zonename))
        return
    record_ipv4 = get_zone_host_data(token, hostname, "A")[4]
    
    # TODO: handle edge cases where zone does not have an A resource record
    
    # get external ipv4 address
    ipv4 = requests.get('https://api.ipify.org').content.decode('utf8')
    
    # get global ipv6 address
    ipv6 = addresses[netifaces.AF_INET6]    
    for ip in ipv6:
        try:
            ip = ipaddress.IPv6Address(ip["addr"])
            if ip.is_global:
                ipv6 = str(ip)
        except ipaddress.AddressValueError:
            pass
    
    # update if there is a new IPv4
    if ipaddress.IPv4Address(record_ipv4) != ipaddress.IPv4Address(ipv4):
        url = "https://dynv6.com/api/v2/zones/{0}".format(zone_id)
        
        # updates auto-set ipv4 records
        # ipv6 required in payload, otherwise patching primary zone record won't work
        # TODO: make options so users can update the ipv4 and v6 primary zone records independently if needed
        payload = {"ipv4address": ipv4, "ipv6prefix": ipv6}
        header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
        r = requests.patch(url, data=payload, headers=header)
        
        #TODO: make option to update A resource records independent of primary zone records (for non-auto-set ipv4 records)
        
        if r.status_code == 200:
            print("Record for {} changed to {}".format(hostname, ipv4))
        else:
            print("Updating IPv4 address failed with error {}".format(r.status_code))
    else:
        print("IPv4 address unchanged. No action taken.")
    
    # update if there is a new ipv6
    if ipaddress.IPv6Address(record_ipv6) != ipaddress.IPv6Address(ipv6):
        url = "https://dynv6.com/api/v2/zones/{0}/records/{1}".format(zone_id, host_id)
        payload = {"type":"AAAA","name":name,"data":ipv6,"recordID":host_id,"zoneID":zone_id}
        header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
        r = requests.patch(url, data=payload, headers=header)
        if r.status_code == 200:
            print("Record for {} changed to {}".format(hostname, ipv6))
        else:
            print("Updating IPv6 address failed with error {}".format(r.status_code))
    else:
        print("IPv6 address unchanged. No action taken.")

def get_zone_host_data(token, hostname, r_type = "AAAA"):
    zones = ""
    host_id = ""
    zone_id = ""
    record_data = ""
    
    zonename = ".".join(hostname.split(".")[1:])
    name = hostname.split(".")[0]
    
    # get zones
    header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
    z_response = requests.get("https://dynv6.com/api/v2/zones", headers=header)
    if z_response.status_code == 200:
        zones = z_response.json()
        
        # in case user is updating the root record
        if not any(zone["name"] == zonename for zone in zones):
            zonename = hostname
            name = ""
            
        for zone in zones:
            if zone["name"] == zonename:
                id = zone["id"]
                url = "https://dynv6.com/api/v2/zones/{}/records".format(id)
                r_response = requests.get(url, headers=header)
                if r_response.status_code == 200:
                    records = r_response.json()
                    for record in records:
                        if record["name"] == name and record["type"] == r_type:
                            host_id = record["id"]
                            record_data = record["data"]
                            zone_id = id
                
                            # get expandedData from auto-set records
                            if record_data == "" and r_type == "A":
                                record_data = record["expandedData"]
                                
    return zonename, zone_id, name, host_id, record_data

if __name__ == '__main__':
    main()
