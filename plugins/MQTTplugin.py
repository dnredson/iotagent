import sys
import time
import json
import requests
import docker
import threading
import paho.mqtt.client as mqtt

print("Iniciando monitoramento mqtt")

if len(sys.argv) != 10:
    print("Número incorreto de argumentos fornecidos.")
    sys.exit(1)

service_name, service_address, service_port, service_path, service, broker_address, entity_id, sample_interval,parent_infra = sys.argv[1:]
print(service_name, service_address, service_port, service_path, service, broker_address, entity_id, sample_interval,parent_infra)
service_port = int(service_port)
sample_interval = int(sample_interval)
print("Starting Monitoring Service for "+str(service_name)+" every "+str(sample_interval)+" seconds")
client = docker.from_env()
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def on_message(client, userdata, message):
    global message_received
    
    if message.payload.decode() == "ok":
        message_received = True

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
        
def publish_message(broker_address, broker_port):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,"Publisher")
    
    client.connect(broker_address, broker_port)
    client.loop_start()
    client.publish("testavailable", "ok")
    time.sleep(2)  # Aguarda um pouco para garantir que a mensagem foi enviada
    client.loop_stop()

def subscribe_to_topic(broker_address, broker_port):
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1,"Subscriber")
    #client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_address, broker_port)
    client.subscribe("testavailable")
    client.loop_start()
    time.sleep(2) 

def test_mqtt_broker(broker_address, broker_port):
    global message_received
    message_received = False
    threading.Thread(target=subscribe_to_topic, args=(broker_address, broker_port)).start()
    time.sleep(1)  # Aguarda um pouco antes de publicar
    publish_message(broker_address, broker_port)
    time.sleep(2)  # Aguarda para ver se a mensagem foi recebida
   
    if message_received:
        return True
    else:
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
        "availability": {"type": "boolean", "value": availability},
        "parentInfra": {"type": "Number", "value": parent_infra},
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
    
    cpu_percent, memory_percent = collect_metrics(service_name)
    mqtt_status = test_mqtt_broker(service_address,service_port)
    
    create_or_update_entity(cpu_percent, memory_percent,mqtt_status)
    
    elapsed_time = time.time() - start_time
    sleep_time = max(0, sample_interval - elapsed_time)
    
    time.sleep(sample_interval)
