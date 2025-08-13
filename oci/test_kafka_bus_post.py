#!/usr/bin/env python3

import requests
import json

def post_to_kafka():
    """
    curl -sLk -X POST bridge-bridge-service.telem.svc.cluster.local:8080/topics/metricreports -H "Content-Type: application/vnd.kafka.json.v2+json"  -d '{ "records": [ { "key": "my-key", "value": "my-value" } ] }'
    """
    url = "http://bridge-bridge-service.telem.svc.cluster.local:8080/topics/metricreports"
    headers = {
        "Content-Type": "application/vnd.kafka.json.v2+json",
    }
    file = "/MetricReports/192.168.187.19/8R3KPR3/GPUMetrics/GPUMetrics.68"
    with open(file, 'r') as fh: 
        data = json.load(fh)
    payload = {
        "records": [ 
            {
                "key": "my-key", 
                "value": data
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Message sent successfully!")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

if __name__ == '__main__':
    post_to_kafka() 
