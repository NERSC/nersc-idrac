#!/usr/bin/env python3
import socket

def ip_to_hostname(ip_address):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except socket.herror:
        return "Hostname not found"

if __name__ == '__main__':
    # Example usage:
    ip = "8.8.8.8"
    hostname = ip_to_hostname(ip)
    print(f"The hostname for {ip} is: {hostname}") # Output: The hostname for 8.8.8.8 is: google-public-dns-a.google.com
    
    ip = "192.168.187.14"
    hostname = ip_to_hostname(ip)
    print(f"The hostname for {ip} is: {hostname}") # Output: The hostname for 192.168.1.1 is: Hostname not found


