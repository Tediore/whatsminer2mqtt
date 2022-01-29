# MIT License

# whatsminer-api Copyright (c) 2021 satoshi-anonymoto

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import json
import logging
from time import sleep
from threading import Thread as t
import paho.mqtt.client as mqtt_client
from whatsminer import WhatsminerAccessToken, WhatsminerAPI

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_KEEPALIVE = int(os.getenv('INTERVAL')) * 3
BASE_TOPIC = os.getenv('BASE_TOPIC', 'whatsminer')
MINER_IP = os.getenv('MINER_IP')
HOME_ASSISTANT = os.getenv('HOME_ASSISTANT', True)
INTERVAL = int(os.getenv('INTERVAL', 10))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

class Whatsminer:
    def __init__(self):
        self.old_info = {}

    def get_info(self):
        """Gather data from Whatsminer API"""
        try:
            output = WhatsminerAPI.get_read_only_info(access_token=token, cmd="summary")
            status = output['STATUS'][0]
            summary = output['SUMMARY'][0]
            self.info = status | summary
        except Exception as e:
            logging.error(f'Unable to connect to Whatsminer API: {e}')

    def send_payload(self):
        """Send MQTT payload for each parameter from Whatsminer API if value changed from previous payload"""
        try:
            for x, y in self.info.items():
                try:
                    if y != self.old_info[x]:
                        client.publish(f'{BASE_TOPIC}/info/{x}', payload=str(y), qos=0, retain=True)
                except KeyError:
                    # if key doesn't exist in previous payload (e.g., this is the first time whatsminer2mqtt has sent a payload since startup), ignore 
                    # the error and send the payload
                    client.publish(f'{BASE_TOPIC}/info/{x}', payload=str(y), qos=0, retain=True)
            client.publish(f'{BASE_TOPIC}/status', 'online', 0, True)
            self.old_info = self.info
        except Exception as e:
            logging.error(f'Unable to publish payload (send_payload): {e}')

    def mqtt_discovery(self):
        """Send Home Assistant MQTT discovery payloads"""
        try:
            for x in self.info.keys():
                client.publish(f'homeassistant/sensor/Whatsminer_{MINER_IP.replace(".","-")}/{x.replace(" ","")}/config', payload=json.dumps({
                    'availability': [
                        {'topic': f'{BASE_TOPIC}/status'}
                    ],
                    'name': f'Whatsminer {x}',
                    'state_topic': f'{BASE_TOPIC}/info/{x}',
                    'unique_id': f'{MINER_IP}{x}',
                    'device': {
                        'name': f'Whatsminer {MINER_IP}',
                        'identifiers': f'Whatsminer {MINER_IP}',
                        'manufacturer': 'Whatsminer',
                        'sw_version': '1.0',
                        'model': 'Whatsminer'
                    }
                }
                ), qos=0, retain=True)
        except Exception as e:
            logging.error(f'Unable to publish MQTT discovery payload: {e}')

def mqtt_connect():
    """Connect to MQTT broker and set LWT"""
    try:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.will_set(f'{BASE_TOPIC}/status', 'offline', 0, True)
        client.on_connect = on_connect
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
        client.publish(f'{BASE_TOPIC}/status', 'online', 0, True)
    except Exception as e:
        logging.error(f'Unable to connect to MQTT broker: {e}')
        sys.exit()

def on_connect(client, userdata, flags, rc):
    # The callback for when the client receives a CONNACK response from the MQTT broker.
    logging.info('Connected to MQTT broker with result code ' + str(rc))

def main_loop():
    """Poll for info from the Whatsminer API at defined interval"""
    while True:
        sleep(INTERVAL)
        w.send_payload()

if __name__ == '__main__':
    if MQTT_HOST == None:
        logging.error('Please specify the IP address or hostname of your MQTT broker.')
        sys.exit()

    if LOG_LEVEL.lower() not in ['debug', 'info', 'warning', 'error']:
        logging.basicConfig(level='INFO', format='%(asctime)s %(levelname)s: %(message)s')
        logging.warning(f'Selected log level "{LOG_LEVEL}" is not valid; using default (INFO)')
    else:
        logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s: %(message)s')

    client = mqtt_client.Client(BASE_TOPIC)
    token = WhatsminerAccessToken(ip_address=MINER_IP)
    w = Whatsminer()
    mqtt_connect()
    w.get_info()
    w.send_payload()
    if HOME_ASSISTANT:
        w.mqtt_discovery()
    polling_thread = t(target=main_loop, daemon=True)
    polling_thread.start()
    client.loop_forever()