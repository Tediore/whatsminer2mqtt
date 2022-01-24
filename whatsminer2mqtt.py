import os
import sys
import json
import logging
from time import sleep
import paho.mqtt.client as mqtt_client
from whatsminer import WhatsminerAccessToken, WhatsminerAPI

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_KEEPALIVE = int(os.getenv('INTERVAL')) * 2
MQTT_QOS = int(os.getenv('MQTT_QOS', 1))
BASE_TOPIC = os.getenv('BASE_TOPIC', 'whatsminer')
MINER_IP = os.getenv('MINER_IP')
MINER_TOKEN = os.getenv('MINER_TOKEN')
HOME_ASSISTANT = os.getenv('HOME_ASSISTANT', True)
INTERVAL = int(os.getenv('INTERVAL', 10))

client = mqtt_client.Client(BASE_TOPIC)
token = WhatsminerAccessToken(ip_address=MINER_IP)

def mqtt_connect():
    """Connect to MQTT broker and set LWT"""
    try:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.will_set(f'{BASE_TOPIC}/status', 'offline', 1, True)
        client.on_connect = on_connect
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
        client.publish(f'{BASE_TOPIC}/status', 'online', 1, True)
    except Exception as e:
        logging.error(f'Unable to connect to MQTT broker: {e}')
        sys.exit()

def on_connect(client, userdata, flags, rc):
    # The callback for when the client receives a CONNACK response from the MQTT broker.
    logging.info('Connected to MQTT broker with result code ' + str(rc))

def get_info():
    summary = WhatsminerAPI.get_read_only_info(access_token=MINER_TOKEN, cmd="summary")
    output = json.dumps(summary)
    return output

try:
    mqtt_connect()
except Exception as e:
    logging.error(f'Unable to connect to MQTT broker: {e}')
    sys.exit()

if HOME_ASSISTANT:
    try:
        output = get_info()
        status = output['STATUS'][0]
        summary = output['SUMMARY'][0]
        id = output['id']
        merge = status | summary
        for x, y in merge.items():
            client.publish(f'{BASE_TOPIC}/info', payload=json.dumps(merge), qos=MQTT_QOS, retain=False)
    except Exception as e:
        logging.error(f'Unable to connect to Whatsminer API: {e}')
        sys.exit()

    for x, y in merge.items():
        client.publish(f'homeassistant/sensor/{MINER_IP}/config', payload=json.dumps({
            'availability': [
                {'topic': f'{BASE_TOPIC}/status'}
            ],
            'name': f'Whatsminer {x}',
            'state_topic': f'{BASE_TOPIC}/info',
            'state_value_template': f'{{ value_json[{y}] }}',
            'unique_id': f'{MINER_IP}{x}',
            'device': {
                'name': f'Whatsminer {MINER_IP}',
                'identifiers': f'Whatsminer {MINER_IP}',
                'platform': 'mqtt'
            }
        }
        ), qos=MQTT_QOS, retain=True)

while True:
    try:
        payload = get_info()
        client.publish(f'{BASE_TOPIC}/info', payload=payload, qos=MQTT_QOS, retain=True)
    except Exception as e:
        logging.error(f'{e}')
    sleep(INTERVAL)