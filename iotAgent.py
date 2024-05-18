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

""" def get_entity(config):
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
     """
def get_entity(config):
    address = config.get('address', '')
    headers = {
        'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',
    }
    while True:
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
            print("Tentando novamente em 10 segundos...")
            time.sleep(10)
#Função para modificar status, ação e tipo de ação dentro de actionMetadata    

# Função parakp
#  consultar a entidade no Fiware-Orion
def consultar_fiware_orion(service_id):
    
    url = f"http://192.168.10.105:1026/v2/entities/{service_id}"
    headers = {
        'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',
    }
    response = requests.get(url,headers=headers)
   
    if response.status_code == 200 or response.status_code == 204:
   
        return response.json()
    else:
   
        print(f"Erro ao consultar a entidade: {response.status_code}")
        return None


def publicar_fiware_orion(entity):
    url = f"http://192.168.10.105:1026/v2/entities?options=upsert"
    headers = {
        'Content-Type': 'application/json',
        'Fiware-service': 'openiot',
        'Fiware-servicepath': '/',
    }
    response = requests.post(url, headers=headers, json=entity)
    if response.status_code in [200, 204]:
        print("Entidade atualizada com sucesso")
    else:
        print(f"Erro ao atualizar a entidade: {response.status_code}")

def atualizar_campo(entity, service_name, campo, novo_valor):
    # Procura o serviço específico dentro de actionMetadata
    
    for item in entity["actionMetadata"]["value"]:
        if item.get("serviceName") == service_name:
            # Atualiza o campo com o novo valor
            item[campo] = novo_valor
            break
    else:
        print(f"ServiceName '{service_name}' não encontrado em actionMetadata")
    
    # Publica a entidade atualizada no FIWARE Orion
    publicar_fiware_orion(entity)

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



def run_plugin(command):
    print("Running plugin")
    print(command)
    try:
        result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        
        if stdout:
            print("Saída padrão:")
            print(stdout.decode())
        if stderr:
            print("Erro padrão:")
            print(stderr.decode())
    except Exception as e:
        print(f"Erro ao executar o comando: {e}")

def run_plugin(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        returncode = result.returncode

        print("Código de retorno:", returncode)
        print("Saída padrão:", result.stdout)
        print("Saída de erro:", result.stderr)

        return result.stdout, result.stderr
    except Exception as e:
        print(f"Erro ao executar o comando: {e}")
        return None, str(e)
    
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
        children ="first"
        for child in action_metadata_list:
             if child["serviceName"] != "system":
                  children= children +"/" +child["entityId"]
                   
              

        if entity_data:
            
           
            if(entity_data["action"]["value"]):
                
                
                if(entity_data["actionType"]["value"]=="deploy"):
                
                   # action_interval = 30
                    for i in entity_data["actionMetadata"]["value"]:
                
                        
                        if(i["actionType"]=="deploy"):
                            
                            if(i["processtype"]== "docker"):
                              
                                num_elements = len(i["dependencies"]["value"])
                                dependencies = i["dependencies"]["value"]
                                
                                for dependencia in i["dependencies"]["value"] :
                                    address = dependencia["address"]
                                    field_of_interest = dependencia["fieldOfInterest"]
                                    expected_value = dependencia["expectedValue"]
                                    fieldOfInterestValue = dependencia["fieldOfInterestValue"]
                                
                                    result = consultar_fiware_orion(address)
                                    validator = False
                                    while result is None or expected_value == " ":
                                        
                                        time.sleep(10)
                                        print("Consultando a dependencia por "+address)
                                        result = consultar_fiware_orion(address)
                                        
                                        if(result is None):
                                             print("Aguardando para buscar entidade de dependencia novamente")
                                        else:
                                            print("Entidade retornada")
                                            print(result)
                                            if(dependencia["fieldOfInterest"] =="ip_address"):
                                                if( "parentInfra" in result):
                                                    
                                                    parent = consultar_fiware_orion(result["parentInfra"]["value"])
                                                    
                                                    
                                                    dependencia["fieldOfInterestValue"] = parent["ip_address"]["value"]    
                                                    expected_value = dependencia["fieldOfInterestValue"]       
                                                else:
                                                    print("Não Tem parent Infra")
                                                    dependencia["fieldOfInterestValue"] = result["ip_address"]["value"] 
                                                    expected_value = dependencia["fieldOfInterestValue"]
                                            
                                            else: 
                                                if(result[field_of_interest]["value"] == expected_value):
                                                    dependencia["fieldOfInterestValue"] = result[field_of_interest]["value"]

                                                
                                            
                                                
                                        
                                        
                                print('Encerradas todas as checagens de dependências para '+i["serviceName"] +' iniciando deploy')    
                                teste =True
                                if teste:
                                            
                                            
                                            containerName = i["serviceName"]
                                            servicePort = i["servicePort"]
                                            serviceAddress = i["serviceAddress"]	
                                            print("Iniciando deploy de "+containerName)
                                
                                            dockerImage = i["processMetadata"]["value"][0]["dockerImage"]
                                            
                                            
                                            for x in i["processMetadata"]["value"][0]["preInstallCommands"]:
                                                  
                                                comando = urllib.parse.unquote(x["value"])
                                                subprocess.run(comando, shell=True)
                                            
                                            for y in i["processMetadata"]["value"][0]["command"]:
                                            
                                                    startDecode = urllib.parse.unquote(y["value"])
                                                    
                                                    startDecode = startDecode.replace("serviceName",containerName)
                                                    startDecode = startDecode.replace("servicePort",str(servicePort))
                                                    startDecode = startDecode.replace("dockerImage",dockerImage)
                                                    for dependencia in i["dependencies"]["value"]:

                                                        nome = dependencia["dependsOn"]
                                                        valor = dependencia["fieldOfInterestValue"]
                                                        field = dependencia["fieldOfInterest"]
                                                        
                                                        
                                                        try:
                                                            if(field != "availability"):
                                                                startDecode = startDecode.replace(nome,valor)
                                                                print("Start decode com o novo método")
                                                                print(startDecode)
                                                        except ValueError:
                                                             print("Error decoding")
                                                       
                                                    resultado  = subprocess.run(startDecode, shell=True,capture_output=True)
                                                    
                                                    if resultado.returncode == 0:
                                                        print("Executado com sucesso! Iniciando monitor!")
                                                        print("Saída padrão:", resultado.stdout.decode())
                                                        atualizar_campo(entity_data, i["serviceName"], "actionType", "monitoring")
                                                    else:
                                                        print("Erro ao iniciar monitor!")
                                                        print("Saída de erro:", resultado.stderr.decode())
                                                        
                         
                        if(i["actionType"]=="monitoring"):
                            plugin_info = i["pluginName"]    
                            print("Entidade "+i["serviceName"]+" está em monitoring, comecemos! Iniciando plugin"+ plugin_info )                 
                            

                                
                                   
                            if plugin_info == "mqttPlugin":
                                        print("Iniciando plugin MQTT")
                                        service_name = i['serviceName']
                                        service_address = i['serviceAddress']
                                        service_port = i['servicePort']  # Porta padrão MQTT
                                        service_path = i['servicepath']
                                        service = i['serviceName']
                                        parent_infra = i['parentInfra']
                                        broker_address = i['brokerAddress']
                                        entity_id = i['entityId']
                                        sample_interval = i['sampleInterval']
                                        if service_name not in active_plugins:
                                            active_plugins.add(service_name)
                                            subprocess.Popen(['python3', 'plugins/MQTTPlugin.py', service_name, service_address, str(service_port), service_path, service, broker_address, entity_id, str(sample_interval),parent_infra])
                            elif  plugin_info == "dockerMongoPlugin":
                                        print("Iniciando plugin docker Mongo")
                                        service_name = i['serviceName']
                                        service_address = i['serviceAddress']
                                        service_port = i['servicePort']  # Porta padrão MQTT
                                        service_path = i['servicepath']
                                        service = i['serviceName']
                                        broker_address = i['brokerAddress']
                                        parent_infra = i['parentInfra']
                                        entity_id = i['entityId']
                                        sample_interval = i['sampleInterval']
                                        if service_name not in active_plugins:
                                            active_plugins.add(service_name)
                                            subprocess.Popen(['python3', 'plugins/dockerMongoPlugin.py', service_name, service_address, str(service_port), service_path, service, broker_address, entity_id, str(sample_interval),parent_infra])
                            elif  plugin_info == "dockerRestPlugin":
                                        print("Iniciando plugin Docker Rest Plugin")
                                        service_name = i['serviceName']
                                        parent_infra = i['parentInfra']
                                        service_address = i['serviceAddress']
                                        service_port = i['servicePort']  # Porta padrão MQTT
                                        service_path = i['servicepath']
                                        service = i['serviceName']
                                        broker_address = i['brokerAddress']
                                        entity_id = i['entityId']
                                        sample_interval = i['sampleInterval']
                                        healthcheck=""
                                        for meta in i["processMetadata"]["value"]:
                                            healthcheck = meta["healthCheck"]
                                        if service_name not in active_plugins:
                                            
                                            active_plugins.add(service_name)
                                            subprocess.Popen(['python3', 'plugins/dockerRestPlugin.py', service_name, service_address, str(service_port), service_path, service, broker_address, entity_id, str(sample_interval),healthcheck,parent_infra])
                            elif  plugin_info == "systemPlugin":
                                        print("Iniciando plugin System Plugin")
                                        service_name = i['serviceName']
                                        broker_address = i['brokerAddress']
                                        entity_id = i['entityId']
                                        sample_interval = i['sampleInterval']
                                        
                                        if service_name not in active_plugins:
                                            
                                            active_plugins.add(service_name)
                                            subprocess.Popen(['python3', 'plugins/systemPlugin.py', str(sample_interval),  entity_id, broker_address,children])               
                                            
                            elif  plugin_info == "systemPluginAWS":
                                        service_name = i['serviceName']
                                        broker_address = i['brokerAddress']
                                        entity_id = i['entityId']
                                        sample_interval = i['sampleInterval']
                                        print(children)

                                        print("Iniciando System AWS Plugin")
                                        if service_name not in active_plugins:
                                            
                                            active_plugins.add(service_name)
                                            subprocess.Popen(['python3', 'plugins/systemPluginAWS.py', str(sample_interval),  entity_id, broker_address,children])               
                            else:
                                        print("Plugin não encontrado: ",plugin_info)
                                        print("Atualmente monitorando: ")
                                        print(active_plugins)
                                        
                        else:
                            print("Action type definido não tem nenhuma config definida")

        
        time.sleep(action_interval)
        

if __name__ == "__main__":
    main()
