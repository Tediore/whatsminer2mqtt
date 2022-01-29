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
MQTT_KEEPALIVE = int(os.getenv('INTERVAL')) * 5
BASE_TOPIC = os.getenv('BASE_TOPIC', 'whatsminer')
MINER_IP = os.getenv('MINER_IP')
HOME_ASSISTANT = os.getenv('HOME_ASSISTANT', True)
INTERVAL = int(os.getenv('INTERVAL', 10))

client = mqtt_client.Client(BASE_TOPIC)
token = WhatsminerAccessToken(ip_address=MINER_IP)

logging.basicConfig(level='INFO', format='%(asctime)s %(levelname)s: %(message)s')

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

def get_info():
    try:
        output = WhatsminerAPI.get_read_only_info(access_token=token, cmd="summary")
        status = output['STATUS'][0]
        summary = output['SUMMARY'][0]
        # status = {'STATUS': 'S', 'When': 1643347157, 'Code': 11, 'Msg': 'Summary', 'Description': 'cgminer 4.9.2'}
        # summary = {'Elapsed': 394368, 'MHS av': 54950457.69, 'MHS 5s': 56199295.48, 'MHS 1m': 54747047.59, 'MHS 5m': 54844639.42, 'MHS 15m': 54780205.41, 'HS RT': 54844639.42, 'Found Blocks': 0, 'Getworks': 25952, 'Accepted': 148655, 'Rejected': 37, 'Hardware Errors': 904, 'Utility': 22.62, 'Discarded': 19039575, 'Stale': 2, 'Get Failures': 4, 'Local Work': 2660323345, 'Remote Failures': 0, 'Network Blocks': 654, 'Total MH': 21670690782991.0, 'Work Utility': 2998.63, 'Difficulty Accepted': 5054381082.0, 'Difficulty Rejected': 1333251.0, 'Difficulty Stale': 0.0, 'Best Share': 3111029565, 'Temperature': 72.0, 'freq_avg': 848, 'Fan Speed In': 6840, 'Fan Speed Out': 6840, 'Voltage': 1228, 'Power': 3412, 'Power_RT': 3416, 'Device Hardware%': 0.0046, 'Device Rejected%': 6.7645, 'Pool Rejected%': 0.0264, 'Pool Stale%': 0.0, 'Last getwork': 0, 'Uptime': 395662, 'Chip Data': 'HPND06-19102101   BINV04-192106B', 'Power Current': 248, 'Power Fanspeed': 8910, 'Error Code Count': 0, 'Factory Error Code Count': 0, 'Security Mode': 0, 'Liquid Cooling': False, 'Hash Stable': True, 'Hash Stable Cost Seconds': 2194, 'Hash Deviation%': -1.022, 'Target Freq': 824, 'Target MHS': 54166464, 'Power Mode': 'Normal', 'Firmware Version': "'20210322.22.REL'", 'CB Platform': 'ALLWINNER_H3', 'CB Version': 'V8', 'MAC': '99:DE:AD:BE:EF:99', 'Factory GHS': 55347, 'Power Limit': 3500, 'Chip Temp Min': 0.0, 'Chip Temp Max': 0.0, 'Chip Temp Avg': 0.0}
        info = status | summary
    except Exception as e:
        logging.error(f'Unable to connect to Whatsminer API: {e}')
    return info

def send_payload():
    info = get_info()
    for x, y in info.items():
        client.publish(f'{BASE_TOPIC}/info/{x}', payload=str(y), qos=0, retain=True)

def mqtt_discovery():
    try:
        info = get_info()
        for x in info.keys():
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

def main_loop():
    while True:
        send_payload()
        sleep(INTERVAL)

if __name__ == '__main__':
    mqtt_connect()
    mqtt_discovery()
    polling_thread = t(target=main_loop, daemon=True)
    polling_thread.start()
    client.loop_forever()