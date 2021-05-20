#!/bin/bash

echo
echo "+======================"
echo "| START: MQTTToMongoDB"
echo "+======================"
echo

source .env
echo "Using args ${CONNSTR}"

docker build -t graboskyc/mqtttomongo:latest .
docker stop mqtttomongo
docker rm mqtttomongo
docker run -t -i -d -p 1883:1883 --name mqtttomongo -e "CONNSTR=${CONNSTR}" --restart unless-stopped graboskyc/mqtttomongo:latest

echo
echo "+======================"
echo "| END: MQTTToMongoDB"
echo "+======================"
echo
