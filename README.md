# MQTTToMongoDB

This is a simple proof of concept to act as a middleware console app to take in IOT sensor data via MQTT (act as a broker) and write those messages into MongoDB to a local MongoDB instance. It also contains a python script which uses Change Streams to send that data to Atlas.

# Setup
## Pre Reqs
* Deploy an Atlas Cluster
* Start a mongodb replica set

## Code Setup
* Clone this repo onto a server
* make a .env file: `cp sample.env .env`
* Edit the .env and replace the values with that of your connection string of your Replica Set
* Run `./build.sh` which will start the docker container for you using the above variables
* Edit the `csSync.py` and change connection strings to point to `src` (local) and `dst` (Atlas)

## Execution
* Point your MQTT clients I mentioned above at this now running MQTT broker