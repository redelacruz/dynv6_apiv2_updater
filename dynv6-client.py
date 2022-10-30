#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import netifaces
import requests
import ipaddress

@click.command()
@click.argument('hostname')
@click.option('-t', '--token', prompt=True, hide_input=True, help='DynV6 HTTP token', metavar='TOKEN')
@click.option('-i', '--interface', default='eth0', help='An interface providing global IPv6 addresses to update HOSTNAME', metavar='INTERFACE')
@click.option('--all-records', is_flag=True, help='Update all resource records for a given HOSTNAME')
#TODO: --manual-ipv4, is_flag=True, help='Update all A resource records independently of the primary zone record, overriding DynV6 auto-set records. Can be used with --all-records.'

def main(hostname, token, interface):
    """Update the DynV6 zone records of HOSTNAME."""
    valid_ipv4 = False
    valid_ipv6 = False
    valid_record_ipv4 = False
    valid_record_ipv6 = False
    
    addresses = netifaces.ifaddresses(interface)
    
    # Get current zone addresses
    zone_name, zone_id, record_name, record_id, record_ipv6 = get_zone_record_data(token, hostname)
    if not zone_id:
        print("Zone does not exist. Check the zone and try again.")
        return
    if not record_id:
        print("Host does not exist in {}. Check the host and try again.".format(zone_name))
        return
    record_ipv4 = get_zone_record_data(token, hostname, "A")[4]
    
    # Check if record_ipv4 is auto-set
    autoset_ipv4 = False
    if "x" in record_ipv4:
        autoset_ipv4 = True
        record_ipv4 = record_ipv4[1:]
    
    # TODO: handle edge cases where zone does not have an A resource record
    
    # Get external IPv4 address
    ipv4 = requests.get('https://api.ipify.org').content.decode('utf8')
    try:
        ipv4 = ipaddress.IPv4Address(ipv4["addr"])
        ipv4 = str(ipv4)
        valid_ipv4 = True
    except ipaddress.AddressValueError:
        pass
    
    # Get global IPv6 address
    ipv6 = addresses[netifaces.AF_INET6]    
    for ip in ipv6:
        try:
            ip = ipaddress.IPv6Address(ip["addr"])
            if ip.is_global:
                ipv6 = str(ip)
                valid_ipv6 = True
        except ipaddress.AddressValueError:
            pass
    
    # Check validity of retrieved IPv4 record
    try:
        record_ipv4 = ipaddress.IPv4Address(record_ipv4["addr"])
        record_ipv4 = str(record_ipv4)
        valid_record_ipv4 = True
    except ipaddress.AddressValueError:
        pass
        
    # Check validity of retrieved IPv6 record
    try:
        record_ipv6 = ipaddress.IPv6Address(record_ipv6["addr"])
        record_ipv6 = str(record_ipv6)
        valid_record_ipv6 = True
    except ipaddress.AddressValueError:
        pass
    
    # TODO: Define behavior based on validity of IP addresses collected
    
    
    # Update if there is a new IPv4
    if ipaddress.IPv4Address(record_ipv4) != ipaddress.IPv4Address(ipv4):
    # TODO
    else:
        print("IPv4 address unchanged. No action taken.")
        
    # Update if there is a new IPv6
    if ipaddress.IPv6Address(record_ipv6) != ipaddress.IPv6Address(ipv6):
    # TODO
    else:
        print("IPv6 address unchanged. No action taken.")
            
def update_zone(token, zone_name, zone_id, ipv4, ipv6):
    """
    Updates the primary records of a given zone.
    Requires both IPv4 and IPv6 addresses due to PATCH requests failing quietly when
    one or the other is missing (not in DynV6 REST API documention; probably a bug).
    """
    url = "https://dynv6.com/api/v2/zones/{0}".format(zone_id)
    payload = {"ipv4address": ipv4, "ipv6prefix": ipv6}
    header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
    r = requests.patch(url, data=payload, headers=header)
    
    if r.status_code == 200:
        print("Successfully updated primary records for {}".format(zone_name))
    else:
        print("Updating primary zone records failed with error {}".format(r.status_code))
            
def update_ipv4(token, hostname, record_name, zone_id, record_id, ipv4):
    """Updates the IPv4 A record of the given hostname. Overrides auto-set A records."""
    url = "https://dynv6.com/api/v2/zones/{0}/records/{1}".format(zone_id, record_id)
    payload = {"type":"A","name":record_name,"data":ipv4,"recordID":record_id,"zoneID":zone_id}
    header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
    r = requests.patch(url, data=payload, headers=header)
    
    if r.status_code == 200:
        print("Record for {} changed to {}".format(hostname, ipv4))
    else:
        print("Updating IPv4 address failed with error {}".format(r.status_code))

def update_ipv6(token, hostname, record_name, zone_id, record_id, ipv6):
    """Updates the IPv6 AAAA record of the given hostname."""
    url = "https://dynv6.com/api/v2/zones/{0}/records/{1}".format(zone_id, record_id)
    payload = {"type":"AAAA","name":record_name,"data":ipv6,"recordID":record_id,"zoneID":zone_id}
    header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
    r = requests.patch(url, data=payload, headers=header)
    if r.status_code == 200:
        print("Record for {} changed to {}".format(hostname, ipv6))
    else:
        print("Updating IPv6 address failed with error {}".format(r.status_code))

def get_zone_record_data(token, hostname, r_type = "AAAA", zone_only = False):
    """Get a resource record for a given hostname."""
    zones = ""
    record_id = ""
    zone_id = ""
    record_data = ""
    
    zone_name = ".".join(hostname.split(".")[1:])
    record_name = hostname.split(".")[0]
    
    # Get zones
    header = {"Authorization": "Bearer {}".format(token), "Accept": "application/json"}
    z_response = requests.get("https://dynv6.com/api/v2/zones", headers=header)
    if z_response.status_code == 200:
        zones = z_response.json()
        
        # In case user is updating the root record
        if not any(zone["name"] == zone_name for zone in zones):
            deep_search = True
            
        for zone in zones:
        
            # Get correct names for subdomains 2 levels lower than the primary zone name
            if deep_search:
                s = hostname.split(".")
                for i in reversed(range(len(s) - 1)):
                    zone_name = ".".join(s[i:])
                    if zone["name"] == zone_name:
                        record_name = ".".join(s[:i])
                        break
                
            
            if zone["name"] == zone_name:
                id = zone["id"]
                
                # Return zone data
                if zone_only:
                    return zone_name, id, zone["ipv4address"], zone["ipv6prefix"]
                
                url = "https://dynv6.com/api/v2/zones/{}/records".format(id)
                r_response = requests.get(url, headers=header)
                if r_response.status_code == 200:
                    records = r_response.json()
                    for record in records:
                        if record["name"] == record_name and record["type"] == r_type:
                            record_id = record["id"]
                            record_data = record["data"]
                            zone_id = id
                
                            # Get expandedData from auto-set records
                            if record_data == "" and r_type == "A":
                                record_data = "x{}".format(record["expandedData"])
                                
                            break
                    break
                                
    return zone_name, zone_id, record_name, record_id, record_data

if __name__ == '__main__':
    main()
