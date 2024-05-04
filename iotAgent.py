import json
import requests
import subprocess
import urllib.parse
import time 

active_plugins = set()
def load_config(filename):
    with open(filename, 'r') as file:
        config = json.load(file)
    return config

def get_entity(config):
    address = config.get('address', '')
    headers = {
        'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',
    }
    response = requests.get(f"{address}/{config['config_entity']}", headers=headers)
    if response.status_code == 200:
        entity_data = response.json()
        if isinstance(entity_data, list):
            # Se a resposta for uma lista, pegamos o primeiro elemento
            entity_data = entity_data[0]
        print("Entidade do Orion obtida:", entity_data.get('id'))
        return entity_data
    else:
        print("Erro ao obter a entidade do Orion:", response.text)
        return None
    
#Função para modificar status, ação e tipo de ação dentro de actionMetadata    
def modify_and_publish_entity(entity,service_name, action_type, status,action):
   if action :
    
    # Modifica a entidade localmente
    for item in entity['value']:
       
        if item['serviceName'] == service_name:
            item['actionType'] = action_type
            item['status'] = status
            item['action'] =  action
            

    # Publica a entidade modificada no Orion
    url = 'http://192.168.10.105:1026/v2/entities/urn:ngsi-ld:Fog1/attrs/'
    headers = {'Content-Type': 'application/json',
                'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',}
    completePay= {
        "actionMetadata": entity
    }
    payload = json.dumps(completePay)
    
    try:
        response = requests.patch(url, headers=headers, data=payload)
        if response.status_code == 204:
            print("Entidade modificada e publicada com sucesso no Orion.")
        else:
            print("Erro ao publicar a entidade no Orion:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Erro ao fazer a requisição para o Orion:", e)


def update_entity_action_type(broker,entity,value):
    payload = {"actionType": {"type": "Text", "value": value}}
    headers = {
        'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',
    }
    response = requests.patch(f"{broker}/{entity}/attrs", headers=headers, json=payload)
    if response.status_code not in [204, 200]:
        print(f"Erro ao atualizar a entidade: {response.status_code}")
    else:
        print("Entidade atualizada! Deploy realizado")

def update_entity_action(broker,entity,value):
    payload = {"action": {"type": "Boolean", "value": value}}
    headers = {
        'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',
    }
    response = requests.patch(f"{broker}/{entity}/attrs", headers=headers, json=payload)
    if response.status_code not in [204, 200]:
        print(f"Erro ao atualizar a entidade: {response.status_code}")
    else:
        print("Entidade atualizada! Deploy realizado")

def main():
    config_filename = 'config.json'
    config = load_config(config_filename)


    
   
    while True:
       
        entity_data = get_entity(config)
        config_broker_address = config["address"]
        config_entityId = config["config_entity"]
        action_metadata = entity_data['actionMetadata']
        action_metadata_list = action_metadata['value']
        first_item = action_metadata_list[0]
        plugin_name = first_item['pluginName']
        action_interval = int(entity_data['action_interval']["value"])
        if entity_data:
            
           
            if(entity_data["action"]["value"]):
                
                if(entity_data["actionType"]["value"]=="deploy"):
                    action_interval = 30
                    for i in entity_data["actionMetadata"]["value"]:
                        
                        if(i["actionType"]=="deploy"):
                            if(i["processtype"]=="docker"):

                                containerName = i["serviceName"]
                                servicePort = i["servicePort"]
                                serviceAddress = i["serviceAddress"]	
                            
                                
                                dockerImage = i["processMetadata"]["value"][0]["dockerImage"]
                                for x in i["processMetadata"]["value"][0]["preInstallCommands"]:
                                    
                                    comando = urllib.parse.unquote(x["value"])
                                    subprocess.run(comando, shell=True)
                                for y in i["processMetadata"]["value"][0]["command"]:
                                    startDecode = urllib.parse.unquote(y["value"])
                                    startDecode = startDecode.replace("serviceName",containerName)
                                    startDecode = startDecode.replace("servicePort",str(servicePort))
                                    startDecode = startDecode.replace("dockerImage",dockerImage)
                                  
                                    resultado  = subprocess.run(startDecode, shell=True,capture_output=True)
                                    if resultado.returncode == 0:
                                        print("Iniciando monitor!")
                                        print("Saída padrão:", resultado.stdout.decode())
                                    else:
                                        print("Erro ao iniciar monitor!")
                                        print("Saída de erro:", resultado.stderr.decode())
                            modify_and_publish_entity(action_metadata,containerName,"monitoring","deployed","true") 

                    update_entity_action_type(config_broker_address,config_entityId,"monitoring")        
                           
                    
                if(entity_data["actionType"]["value"]=="monitoring"):
                                     
                    for component in entity_data["actionMetadata"]["value"]:

                        
                            plugin_info = component["pluginName"]
                            if plugin_info == 'mqttPlugin':
                    
                                service_name = component['serviceName']
                                service_address = component['serviceAddress']
                                service_port = component['servicePort']  # Porta padrão MQTT
                                service_path = component['servicepath']
                                service = component['serviceName']
                                broker_address = component['brokerAddress']
                                entity_id = component['entityid']
                                sample_interval = component['sampleInterval']
                                if service_name not in active_plugins:
                                    active_plugins.add(service_name)
                                    subprocess.Popen(['python3', 'plugins/mqttPlugin.py', service_name, service_address, str(service_port), service_path, service, broker_address, entity_id, str(sample_interval)])
                            if plugin_info == 'dockerMongoPlugin':
                                
                                service_name = component['serviceName']
                                service_address = component['serviceAddress']
                                service_port = component['servicePort']  # Porta padrão MQTT
                                service_path = component['servicepath']
                                service = component['serviceName']
                                broker_address = component['brokerAddress']
                                entity_id = component['entityid']
                                sample_interval = component['sampleInterval']
                                if service_name not in active_plugins:
                                    active_plugins.add(service_name)
                                    subprocess.Popen(['python3', 'plugins/dockerMongoPlugin.py', service_name, service_address, str(service_port), service_path, service, broker_address, entity_id, str(sample_interval)])
                            if plugin_info == 'dockerRestPlugin':
                              
                                service_name = component['serviceName']
                                service_address = component['serviceAddress']
                                service_port = component['servicePort']  # Porta padrão MQTT
                                service_path = component['servicepath']
                                service = component['serviceName']
                                broker_address = component['brokerAddress']
                                entity_id = component['entityid']
                                sample_interval = component['sampleInterval']
                                healthcheck=""
                                for meta in component["processMetadata"]["value"]:
                                    healthcheck = meta["healthCheck"]
                                if service_name not in active_plugins:
                                    
                                    active_plugins.add(service_name)
                                    subprocess.Popen(['python3', 'plugins/dockerRestPlugin.py', service_name, service_address, str(service_port), service_path, service, broker_address, entity_id, str(sample_interval),healthcheck])
                            if plugin_info == 'systemPlugin':
                              
                                service_name = component['serviceName']
                           
                           
                           
                                broker_address = component['brokerAddress']
                                entity_id = component['entityid']
                                sample_interval = component['sampleInterval']
                           
                                print("Starting System metric plugin")
                                if service_name not in active_plugins:
                                    
                                    active_plugins.add(service_name)
                                    subprocess.Popen(['python3', 'plugins/systemPlugin.py', str(sample_interval),  entity_id, broker_address])
                                           
                            else:
                                print("Plugin não encontrado: ",plugin_info)
                else:
                    print("Action type definido não tem nenhuma config definida")

        
        time.sleep(action_interval)
        

if __name__ == "__main__":
    main()
