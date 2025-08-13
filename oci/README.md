Build:
---

```console
build_and_publish.bash
```

Files:
---

```console
build_and_publish.bash      Script reads Dockerfile.idrac_to_kafka to build contianer image
Dockerfile.idrac_to_kafka   Package flask app in a container
requirements.txt            Python module requirements
server.py                   Listens for idrac MetricEvents and Notificaitons and publishes on kafka via kafka-bridge  
test_kafka_bus_post.py      Test scirpt
test_reverse_dns.py         Test script
wsgi.py                     WSGI wrapper serving server.py via gunicorn 
```

