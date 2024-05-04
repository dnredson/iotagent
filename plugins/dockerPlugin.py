import subprocess
import time
import sys
import platform
import requests
import json
import argparse
import docker

def check_mongodb_health(address, port):
    try:
        client = pymongo.MongoClient(address, port, serverSelectionTimeoutMS=2000)
        client.server_info()
        return True
    except pymongo.errors.ServerSelectionTimeoutError:
        return False
    
def monitorar_container(tempo, nome_container, nome_entidade, endereco_orion):
    client = docker.from_env()

    try:
        container = client.containers.get(nome_container)
    except docker.errors.NotFound:
        print(f"Container {nome_container} não encontrado.")
        return

    print(f"Monitorando o container {nome_container}...")

    try:
        while True:
            stats = container.stats(stream=False)

            cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
            system_cpu_usage = stats['cpu_stats']['system_cpu_usage']
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']

            cpu_percent = (cpu_usage / system_cpu_usage) * 100
            memory_percent = (memory_usage / memory_limit) * 100

            print(f"Uso de CPU: {cpu_percent:.2f}%, Uso de Memória: {memory_percent:.2f}%")
            data = {
            "id": nome_entidade,
            "type": "CPU",
            "cpu": {
                "type": "Number",
                "value": cpu_percent
            },
            "memory": {
                "type": "Number",
                "value": memory_percent
            }
            }
            headers = {
            'Content-Type': 'application/json',
            'Fiware-Service': 'openiot',
            'Fiware-ServicePath': '/'
            }
            try:
                requests.post(f"{endereco_orion}/v2/entities?options=upsert", data=json.dumps(data), headers=headers)
            except requests.exceptions.RequestException as e:
                print(f"Erro ao postar para o Fiware-Orion: {e}")

            time.sleep(tempo)
    except KeyboardInterrupt:
        print("Monitoramento interrompido.")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Collect the CPU and Memory from a container.")
    parser.add_argument('--tempo', type=int, required=True, help="Tempo em segundos entre os pings")
    parser.add_argument('--nome_container', type=str, required=True, help="Nome do container monitorado")
    parser.add_argument('--nome_entidade', type=str, required=True, help="Nome da entidade para o Orion")
    parser.add_argument('--endereco_orion', type=str, required=True, help="Endereço do Fiware-Orion")
    args = parser.parse_args()
    tempo = args.tempo
    nome_container = args.nome_container
    nome_entidade = args.nome_entidade
    endereco_orion = args.endereco_orion

    monitorar_container(tempo, nome_container, nome_entidade, endereco_orion)
