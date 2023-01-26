#!/usr/bin/python3

import json
from flask import Flask, request, jsonify
from multiprocessing import Process, Pipe, Manager
import requests
from time import sleep
import signal
import logging
import pymongo
from datetime import datetime


logging.basicConfig(level=logging.INFO)
server = None

#logging.info("This is a log message.")



app = Flask(__name__)

def handle_sigint(sig, frame):
    logging.info("SIGINT Handler, shutting down...")
    # stop processes
    server.terminate()
    exit(0)

def subscribe_to_orion(orion_url):
    headers = {'Content-type': 'application/ld+json'}
    subscription = {
                        "description": "Notifica cambiamento dati di temperatura e livello acqua",
                        "type": "Subscription",
                        "entities": [{"type": "WaterObserved"}],
                        "watchedAttributes": ["dateObserved"],
                        "notification": {
                                            "format": "keyValues",
                                            "endpoint": {
                                                "uri": "http://analysis:5050/notification",
                                                "accept": "application/json"
                                            }
                                        },
                        "@context": "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld"
                    }
    done = False
    while not done:
        response = requests.post(orion_url, json=subscription, headers=headers)

        if response.status_code != 201:
            print(f"Error creating subscription: {response.content}")
            sleep(5)
        else:
            logging.info("Subscription created successfully")
            done = True

def create_analyzed_jsons(date, temp, temp_flag, height, height_flag):
    json_file = {
                "id": "urn:ngsi:WaterObserved:MNCA-001",
                "type": "Water",
                "height": {
                    "type": "Property",
                    "value": height
                },
                "heightFlag": {
                    "type": "Property",
                    "value": height_flag
                },
                "observedDate": {
                    "type": "DateTime",
                    "value": date
                },
                "temperature": {
                    "type": "Property",
                    "value": temp
                },
                "temperatureFlag": {
                    "type": "Property",
                    "value": temp_flag
                }
            }
    return json_file

def analysis(payload, means_dict):
    # prelevo i dati
    height = payload['data'][0]['height']
    temp = payload['data'][0]['temperature']
    date = payload['data'][0]['dateObserved']['@value']

    # prelevo i valori in base all'ora
    hour = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").hour
    means = means_dict.get(hour)

    logging.info("---------------  Data: {}  ---------------".format(date))
    # controllo se sono outliers
    height_flag = 0
    if height <= means[0]/100*90 or height >= means[0]/100*110:
        height_flag = 1
        logging.info("OUTLIER | Livello - Valore: {} Media: {} - Differenza: {}".format(height, means[0], height-means[0]))
    else:
        logging.info("NORMALE | Livello - Valore: {} Media: {} - Differenza: {}".format(height, means[0], height-means[0]))

    temp_flag = 0
    if temp <= means[1]/100*90 or temp >= means[1]/100*110:
        temp_flag = 1
        logging.info("OUTLIER | Temperatura - Valore: {} Media: {} - Differenza: {}".format(temp, means[1], temp-means[1]))
    else:
        logging.info("NORMALE | Temperatura - Valore: {} Media: {} - Differenza: {}".format(temp, means[1], temp-means[1]))
    logging.info("------------------------------------------------------------")

    # creo il json
    measure = create_analyzed_jsons(date, temp, temp_flag, height, height_flag)
    return measure

def get_usual_values_from_DB():
    client = pymongo.MongoClient("mongodb://mongo-db:27017/")
    db = client["orion"]
    collection = db["means"]
    cursor = collection.find() # estrae tutti i json della collezione

    means_dict = {} # crea un dizionario
    for document in cursor:
        tmpList = []
        height = document['height']['value']
        temp = document['temperature']['value']
        tmpList.append(height)
        tmpList.append(temp)
        
        date = document['observedDate']['value']
        hour = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").hour

        means_dict[hour] = tmpList # aggiunge una chiave per ogni ora
        # la chiave restituisce una lista con le due medie
        
    logging.info("Valori medi di riferimento estratti.")
    return means_dict

def send_to_Mongo(measure):
    client = pymongo.MongoClient("mongodb://mongo-db:27017/")
    db = client["orion"]

    collection = db["measurements"]
    collection.insert_one(measure)
    logging.info("JSON Analizzato inviato a MongoDB")

def server_process(conn, measurements):
    stored_data = []
    
    @app.route('/notification', methods=['GET', 'POST'])
    def handle_notification():
        if request.method == 'POST':
            data = request.get_json() # legge il json del post
            stored_data.append(data) # salva i json ricevuti

            if len(stored_data) == 25:
                del stored_data[0] # fa in modo che salvi solo gli ultimi 24 json
            conn.send(data) # manda il json al main process tramite pipe
            return "Data received\n"
        elif request.method == 'GET':
            if len(stored_data) == 0:
                return "Nessun dato ricevuto :("
            else:
                return jsonify(stored_data[::-1])

    @app.route('/measure', methods=['GET'])
    def handle_measure():
        if len(measurements) == 0:
            return "Nessun dato analizzato :("
        else:
            return jsonify(measurements[::-1])

    app.run(host='analysis',port=5050)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_sigint)

    orion_url = "http://orion:1026/ngsi-ld/v1/subscriptions/"
    subscribe_to_orion(orion_url)
    
    with Manager() as manager:
        meas = manager.list() # rende la lista disponibile tra processi

        parent_conn, child_conn = Pipe() # crea una pipe
        server = Process(target=server_process, args=(child_conn, meas))
        server.start() # avvia il processo Server Flask (Generic Enabler)
        logging.info("Server Flask pronto a ricevere le notifiche del Context Broker")

        means_dict = get_usual_values_from_DB()

        while True:
            data = parent_conn.recv()
            measure = analysis(data, means_dict)
            meas.append(measure)
            if len(meas) == 25:
                del meas[0] # fa in modo che salvi solo gli ultimi 24 json
            send_to_Mongo(measure)

    exit(1)
