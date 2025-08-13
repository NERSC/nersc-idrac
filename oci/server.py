#!/usr/bin/env python3

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import json
import ssl
import logging
from datetime import datetime
import socket

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config.from_pyfile('/config/config.py', silent=True)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

logging.basicConfig(level=logging.INFO)

import requests                                                                                                                                                                                                                                                       
import json                                                                                                                                                                                                                                                           

# Map string to logging level
LOGLEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

def post_to_kafka(ip_address, data, topic):                                                                                                                                                                                                                                                  
    """                                                                                                                                                                                                                                                               
    curl -sLk -X POST bridge-bridge-service.telem.svc.cluster.local:8080/topics/metricreports -H "Content-Type: application/vnd.kafka.json.v2+json"  -d '{ "records": [ { "key": "my-key", "value": "my-value" } ] }'                                                 
    """                                                                                                                                                                                                                                                               
    url = f"http://bridge-bridge-service.telem.svc.cluster.local:8080/topics/{topic}"                                                                                                                                                                            
    headers = {                                                                                                                                                                                                                                                       
        "Content-Type": "application/vnd.kafka.json.v2+json",                                                                                                                                                                                                         
    }                                                                                                                                                                                                                                                                 
    payload = {                                                                                                                                                                                                                                                       
        "records": [                                                                                                                                                                                                                                                  
            {                                                                                                                                                                                                                                                         
                "key": ip_address,                                                                                                                                                                                                                                      
                "value": data                                                                                                                                                                                                                                         
            }                                                                                                                                                                                                                                                         
        ]                                                                                                                                                                                                                                                             
    }                                                                                                                                                                                                                                                                 
    try:                                                                                                                                                                                                                                                              
        response = requests.post(url, headers=headers, json=payload)                                                                                                                                                                                                  
        response.raise_for_status()  # Raise an exception for bad status codes                                                                                                                                                                                        
        logging.info("Message sent successfully!")
        logging.info(response.json())
    except requests.exceptions.RequestException as e:                                                                                                                                                                                                                 
        logging.error(f"Error sending message: {e}")    


def ip_to_hostname(ip_address, cache_file="hostname_cache.json"):
    """
    Translate ip to hostname.  Cached for efficentcy.
    :param ip_address: ipv4 string
    :return string
    """
    cache = {}
    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)  # Load the cache from file
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # Initialize empty cache if file not found or invalid JSON

    if ip_address in cache:
        return cache[ip_address]  # Return cached hostname
    else:
        try:
            hostname, aliases, ip_addresses = socket.gethostbyaddr(ip_address)
            cache[ip_address] = hostname  # Store the hostname in the cache
            with open(cache_file, "w") as f:
                json.dump(cache, f)  # Save the updated cache to file
            return hostname
        except socket.herror:
            cache[ip_address] = "No domain name found"  # Cache the "not found" result
            with open(cache_file, "w") as f:
                json.dump(cache, f)  # Save the updated cache to file
            return "No domain name found"

@app.route('/', methods=['GET'])
def handle_get():
    if request.remote_addr:
        logging.info(f"Requester IP:  {request.remote_addr}")
        ip_to_hostname(request.remote_addr)        
    if request.headers:
        client_ip = request.headers.get('X-Forwarded-Host', request.remote_addr)
        logging.info(f"Requester IP(from header): {client_ip}")
        logging.info(f"Requester header: {request.headers}")
    return { "response" : "This is a test" }

@app.route('/', methods=['POST'])
def handle_post():
    logging.info(f"Called POST")
    remote_addr = "UNKNOWN"
    if request.remote_addr:
        logging.info(f"Requester IP:  {request.remote_addr}")
        ip_to_hostname(request.remote_addr)        
        remote_addr = request.remote_addr
    if request.headers:
        client_ip = request.headers.get('X-Forwarded-Host', request.remote_addr)
        logging.info(f"Requester IP(from header): {client_ip}")
        logging.info(f"Requester header: {request.headers}")
    data = request.get_json()  # Get JSON data from the request
    logging.info(f"type data: {type(data)}")
    reports_dir="/MetricReports"
    events_dir="/Events"
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(events_dir, exist_ok=True)
    reports_dir_test = ['MetricReportDefinition', 'MetricValues', 'Oem']
    events_dir_test = ['Events', 'Oem']
    if all( key in data for key in reports_dir_test):
        if 'Oem' in data:
            if 'Dell' in data['Oem']:
                if 'ServiceTag' in data['Oem']['Dell']:
                    logging.info("MetricReport")
                    node_dir = os.path.join(reports_dir, remote_addr, data['Oem']['Dell']['ServiceTag'])
                    metric_report_dir = os.path.join(node_dir, data['Id'])
                    metric_report_file = os.path.join(metric_report_dir, f"{data['Id']}.{data['ReportSequence']}")
                    os.makedirs(node_dir, exist_ok=True)
                    os.makedirs(metric_report_dir, exist_ok=True)
                    if app.config.get('save_metricreports', False):
                        with open(metric_report_file, "w") as fh:
                            json.dump(data, fh, indent=4)
                    logging.info(f"Post to kafka: remote_addr:{remote_addr}, data_file:{metric_report_file}")
                    # Tag data with the ip                                                                                                                                                                           
                    data['Oem']['Dell']['Ipv4'] = remote_addr  
                    topic = 'metricreports'
                    post_to_kafka(remote_addr, data, topic)
    elif all(key in data for key in events_dir_test):
        if 'Oem' in data:
            if 'Dell' in data['Oem']:
                if 'ServerHostname' in data['Oem']['Dell']:
                    logging.info("Events")
                    node_dir = os.path.join(events_dir, remote_addr, data['Oem']['Dell']['ServerHostname']) 
                    os.makedirs(node_dir, exist_ok=True)
                    for event in data['Events']:
                        event_time_stamp = event['EventTimestamp']
                        event_id = event['EventId']
                        event_file = os.path.join(events_dir, node_dir, event_id)
                        if app.config.get('save_events', False):
                            with open(event_file, "w") as fh:
                                json.dump(event, fh, indent=4)
                        logging.info(f"Saved Event: {event_file}")
                        # Tag data with the ip                                                                                                                                                                           
                        data['Oem']['Dell']['Ipv4'] = remote_addr  
                        topic = 'events'
                        post_to_kafka(remote_addr, data, topic)
    else:
        logging.info(f"data:{data}")
        if app.config.get('save_other', False):
            with open("foo.log", "a") as fh:
                now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                fh.write(f"{now}:\n{data}\n")
    return 'Data received successfully'

if __name__ == '__main__':
    app.logger.setLevel(LOGLEVEL_MAP.get(app.config.get('loglevel', 'debug')))
    # HTTPS
    app.run(debug=True, ssl_context='adhoc', host='0.0.0.0', port=8088)
    # HTTP
    #app.run(debug=True, host='192.168.187.10', port=8088)
