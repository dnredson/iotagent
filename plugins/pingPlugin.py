import subprocess
import time
import sys
import platform
import requests
import json
import argparse

def pluginPing(tempo, url, nome_entidade, endereco_orion):
    while True:
        # Realiza o ping
        if platform.system().lower() == "windows":
            response = subprocess.run(["ping", "-n", "1", url], stdout=subprocess.PIPE, text=True)
        else:
            response = subprocess.run(["ping", "-c", "1", url], stdout=subprocess.PIPE, text=True)

        success = response.returncode == 0
        try:
            if platform.system().lower() == "windows":
                delay = response.stdout.split("tempo=")[-1].split("ms")[0]
            else:
                delay = response.stdout.split("time=")[-1].split(" ms")[0]
        except IndexError:
            delay = 'N/A'  # Quando não há resposta
        isOn = success
        
        print(f"Success: {success}")
        print(f"Delay: {delay} ")
        
        # Aqui você pode construir o JSON e enviar para o Orion conforme necessário
        data = {
            "id": nome_entidade,
            "type": "PingResult",
            "isSuccessful": {
                "type": "Boolean",
                "value": success
            },
            "responseTime": {
                "type": "Number",
                "value": delay
            }
        }

        # Posta o resultado para o Fiware-Orion
        headers = {
          'Content-Type': 'application/json',
            'Fiware-Service': 'openiot',
            'Fiware-ServicePath': '/'
        }
        try:
            requests.post(f"{endereco_orion}/v2/entities?options=upsert", data=json.dumps(data), headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"Erro ao postar para o Fiware-Orion: {e}")

        # Aguarda o tempo especificado antes do próximo ping
        time.sleep(tempo)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Uso: python ping.py <tempo> <url> <nome_entidade> <endereco_orion>")
        sys.exit(1)
    parser = argparse.ArgumentParser(description="Ping a URL and post the results to a Fiware-Orion instance.")
    parser.add_argument('--tempo', type=int, required=True, help="Tempo em segundos entre os pings")
    parser.add_argument('--url', type=str, required=True, help="URL para fazer o ping")
    parser.add_argument('--nome_entidade', type=str, required=True, help="Nome da entidade para o Orion")
    parser.add_argument('--endereco_orion', type=str, required=True, help="Endereço do Fiware-Orion")
    args = parser.parse_args()
    tempo = args.tempo
    url = args.url
    nome_entidade = args.nome_entidade
    endereco_orion = args.endereco_orion

    pluginPing(tempo, url, nome_entidade, endereco_orion)
