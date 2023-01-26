#!/usr/bin/python3

import math
import random
import time
import datetime
import json
import requests
import logging

logging.basicConfig(level=logging.INFO)

orion_url = "http://orion:1026/ngsi-ld/v1/entities/"
sensor_id = "urn:ngsi:WaterObserved:MNCA-001"

def updateEntity(temp, water_level, date_time):
    headers = {"Content-Type": "application/json"}
    data = {
        "https://smartdatamodels=org/dateObserved":
        {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": date_time
            }
        },
        "https://smartdatamodels.org/dataModel.Environment/height":
        {
            "type": "Property",
            "value": round(water_level*100)
        },
        "https://smartdatamodels=org/dataModel=Environment/temperature":
        {
            "type": "Property",
            "value": round(temp)
        }
    }
    # invio a orion
    done = False
    while not done:
        response = requests.patch("http://orion:1026/ngsi-ld/v1/entities/{}/attrs/".format(sensor_id), headers=headers, json=data)
        if response.status_code == 204:
            logging.info("Entità [ID : {}] aggiornata.".format(sensor_id))
            done = True
        elif response.status_code == 207:
            print("Errore aggiornamento: \n{}".format(response.json()))
            time.sleep(1)
        else:
            print("Errore aggiornamento: {}".format(response.status_code))
            time.sleep(1)

def createEntity(entity_json):
    headers = {'Content-type': 'application/ld+json'}
    done = False
    while not done:
        response = requests.post(orion_url, headers=headers, json=entity_json)
        if response.status_code == 201:
            done = True
            logging.info("Entità [ID: {}] creata con successo su Orion Context Broker.".format(sensor_id))
        else:
            print("Errore creazione: {}".format(response.status_code))
            time.sleep(5)


def create_json_file(temp, water_level, date_time):
    data = {
        "id": sensor_id,
        "type": "WaterObserved",
        "dateObserved":
        {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": date_time
            }
        },
        "height":
        {
            "type": "Property",
            "value": round(water_level*100)
        },
        "temperature":
        {
            "type": "Property",
            "value": round(temp)
        },
        "@context":
        [
            "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld"
        ]
    }
    return data

#simulated_time = datetime.datetime.now().replace(hour=0, minute=0, second=0)
simulated_time = datetime.datetime.now()

# Temperature sensor simulation
previous_temp = None
def temperature_sensor(current_time):
    global previous_temp
    # Generate a temperature based on the current hour
    if previous_temp is None:
        temp = 50
    else:
        temp = previous_temp + random.normalvariate(0, 2)
        temp = min(max(temp, 45), 55)
    previous_temp = temp
    # Add outlier with 5% probability
    if random.random() <= 0.05:
        temp += random.uniform(10, 20)
    return temp

# Water level sensor simulation
previous_water_level = None
def water_level_sensor(current_time):
    global previous_water_level
    if previous_water_level is None:
        water_level = 0.9
    else:
        water_level = previous_water_level + random.normalvariate(0, 0.02)
        water_level = min(max(water_level, 0.6), 1.0)
    previous_water_level = water_level
    # Add outlier with 5% probability
    if random.random() <= 0.05:
        water_level += random.uniform(0.1, 0.3)

    return water_level



# Sample rate
sample_rate = 3


#########################   MAIN   ##########################################

#generazione payload entità
date_time = simulated_time.strftime('%Y-%m-%dT%H:%M:%SZ')
temp = temperature_sensor(simulated_time)
water_level = water_level_sensor(simulated_time)
logging.info("Date and time: {} Temperature: {:.2f}C, Water Level: {:.2f}%".format(date_time, temp, water_level * 100))

#creazione entità su orion
payload = create_json_file(temp, water_level, date_time)
createEntity(payload)

simulated_time += datetime.timedelta(hours=1)
if simulated_time.hour == 0:
    logging.info("\nStart of the new day")
    simulated_time = simulated_time.replace(hour=0, minute=0, second=0)
    simulated_time += datetime.timedelta(days=1)

while True:
    time.sleep(sample_rate)

    # generazione payload nuovi dati
    date_time = simulated_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    temp = temperature_sensor(simulated_time)
    water_level = water_level_sensor(simulated_time)
    logging.info("Date and time: {} Temperature: {:.2f}C, Water Level: {:.2f}%".format(date_time, temp, water_level * 100))

    # aggiornamento dati entità
    updateEntity(temp, water_level, date_time)

    # avanzamento tempo
    simulated_time += datetime.timedelta(hours=1)
    if simulated_time.hour == 0:
        logging.info("\nStart of the new day")
        simulated_time = simulated_time.replace(hour=0, minute=0, second=0)
        simulated_time += datetime.timedelta(days=1)


