#!/bin/bash

# Atualizar a lista de pacotes e instalar os pré-requisitos
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Adicionar a chave GPG oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar o repositório do Docker às fontes do APT
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Atualizar a lista de pacotes com o repositório do Docker adicionado
sudo apt update

# Instalar o Docker CE
sudo apt install -y docker-ce

# Adicionar o usuário atual ao grupo Docker para executar comandos Docker sem sudo
sudo usermod -aG docker $USER

# Instalar o Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar a instalação
docker --version
docker-compose --version
