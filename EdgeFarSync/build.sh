#!/bin/bash

echo
echo "+======================"
echo "| START: Change Stream Sync"
echo "+======================"
echo

echo 
echo "CSCYNC: Building container"
echo
docker build -t graboskyc/mongodb-edgefarsync:latest .

echo 
echo "CSCYNC: Starting container"
echo
docker stop edgefarsync
docker rm edgefarsync
docker run -t -i -d --name edgefarsync --restart unless-stopped -e "ZONENAME=DFW" -e "WATCHZONES=BOS,DEN,FarCloud" -e "CONSTREDGE=mongodb://un:pw@ip:27017" -e "CONSTRFAR=mongodb+srv://un:pw@example.mongodb.net/myFirstDatabase?retryWrites=true&w=majority" graboskyc/mongodb-edgefarsync:latest

echo
echo "+======================"
echo "| END: Change Stream Sync"
echo "+======================"
echo