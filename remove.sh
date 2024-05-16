#!/bin/bash
killall python3
# Parar os containers
docker stop mongodb
docker stop orion

# Remover os containers
docker rm mongodb
docker rm orion
docker ps -a
echo "Containers mongodb e orion foram parados e removidos."
