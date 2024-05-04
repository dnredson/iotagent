import time
import json
import requests
import psutil
import socket
import sys


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def monitorar_sistema(tempo, nome_entidade, endereco_orion):
    print(f"Monitorando as métricas do sistema...")

    while True:
        # Coletar métricas do sistema
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        cpu_cores = psutil.cpu_count(logical=False)

        # Converter memória e disco para MB
        memory_used_mb = memory.used / (1024 * 1024)
        memory_max_mb = memory.total / (1024 * 1024)
        disk_used_mb = disk.used / (1024 * 1024)
        disk_max_mb = disk.total / (1024 * 1024)

        # Obter IP
        ip_address = get_ip_address()

        # Preparar dados para envio
        data = {
            "id": nome_entidade,
            "type": "SystemMetrics",
            "ip_address": {
                "type": "Text",
                "value": ip_address
            },
            "cpu": {
                "type": "Number",
                "value": round(cpu_percent, 2)
            },
            "cpu_frequency": {
                "type": "Number",
                "value": cpu_freq
            },
            "cpu_cores": {
                "type": "Number",
                "value": cpu_cores
            },
            "memory_used": {
                "type": "Number",
                "value": round(memory_used_mb, 2)
            },
            "memory_max": {
                "type": "Number",
                "value": round(memory_max_mb, 2)
            },
            "disk_used": {
                "type": "Number",
                "value": round(disk_used_mb, 2)
            },
            "disk_max": {
                "type": "Number",
                "value": round(disk_max_mb, 2)
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'Fiware-Service': 'openiot',
            'Fiware-ServicePath': '/'
        }

        try:
            response = requests.post(f"{endereco_orion}?options=upsert", data=json.dumps(data), headers=headers)
            print(f"Dados enviados com sucesso: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao postar para o Fiware-Orion: {e}")

        time.sleep(tempo)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python codigo.py tempo nome_entidade endereco_orion")
        sys.exit(1)

    tempo = int(sys.argv[1])
    nome_entidade = sys.argv[2]
    endereco_orion = sys.argv[3]

    monitorar_sistema(tempo, nome_entidade, endereco_orion)
