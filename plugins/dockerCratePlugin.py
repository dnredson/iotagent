import sys
import time
import json
import requests
import docker
import threading
import paho.mqtt.client as mqtt


if len(sys.argv) != 11:
    print("Número incorreto de argumentos fornecidos.")
    sys.exit(1)


service_name, service_address, service_port, service_path, service, broker_address, entity_id, sample_interval, healthcheck,parentInfra = sys.argv[1:]

service_port = int(service_port)
sample_interval = int(sample_interval)
print("Starting Monitoring Service for "+str(service_name)+" every "+str(sample_interval)+" seconds")
client = docker.from_env()

def check_endpoint(healthcheck):
    url = healthcheck
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'stmt': 'SELECT * FROM sys.nodes;'
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print("Erro ao fazer a requisição:", e)
        return False

def collect_metrics(service_name):
    container = client.containers.get(service_name)
    stats = container.stats(stream=False)
    
    
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    number_cpus = stats['cpu_stats']['online_cpus']

    cpu_percent = (cpu_delta / system_cpu_delta) * number_cpus * 100.0

    memory_usage = stats['memory_stats']['usage']
    memory_limit = stats['memory_stats']['limit']
    memory_percent = (memory_usage / memory_limit) * 100.0

    return cpu_percent, memory_percent

def create_or_update_entity(cpu_percent, memory_percent,availability):
    timestamp = time.time()*1000
    
    entity = {
        "id": entity_id,
        "type": "software",
        "serviceName": {"type": "Text", "value": service_name},
        "serviceAddress": {"type": "Text", "value": service_address},
        "cpu": {"type": "Number", "value": round(cpu_percent, 2)},
        "memory": {"type": "Number", "value": round(memory_percent, 2)},
        "availability": {"type": "boolean", "value": check_endpoint(healthcheck)},
        "parentInfra": {"type": "text", "value": parentInfra},
        "timestamp": {"type": "Number", "value": int(timestamp)}
    }
    
    headers = {
        "Content-Type": "application/json",
        "fiware-service": "openiot",
        "fiware-servicepath": "/",
    }
    url = broker_address+"?options=upsert"
   
    response = requests.post(url, headers=headers, json=entity)

    if response.status_code not in (201, 204):
        print(f"Erro ao publicar métricas no Orion: {response.status_code} {response.reason}")
    else:
        print("Métricas atualizadas no Orion com sucesso")

while True:

    start_time = time.time()
    print("Starting new sampling on ",service_name)

    cpu_percent, memory_percent = collect_metrics(service_name)
    status = check_endpoint(healthcheck)
    
    create_or_update_entity(cpu_percent, memory_percent,status)
    
    elapsed_time = time.time() - start_time
    sleep_time = max(0, sample_interval - elapsed_time)
    
    time.sleep(sample_interval)
