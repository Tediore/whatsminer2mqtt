# Whatsminer to MQTT Gateway

whatsminer2mqtt enables data from the unofficial Whatsminer API to be polled and pushed to MQTT. Special thanks to Satoshi Anonymoto for creation of the unofficial Whatsminer API (https://github.com/satoshi-anonymoto/whatsminer-api)

# How to run

**Docker via `docker-compose` (RECOMMENDED)**

1. Create your docker-compose.yaml (or add to existing). Example docker-compose.yaml with all environmental variables:
```yaml
version: '3'
services:
  whatsminer2mqtt:
    container_name: whatsminer2mqtt
    image: tediore/whatsminer2mqtt:latest
    environment:
    - MQTT_HOST=10.0.0.2
    - MQTT_PORT=1883
    - MQTT_USER=user
    - MQTT_PASSWORD=password
    - BASE_TOPIC=whatsminer2mqtt
    - HOMEASSISTANT=True
    - MINER_IP=10.0.1.4
    - INTERVAL=10
    - LOG_LEVEL=debug
    restart: unless-stopped
```
2. `docker-compose up -d whatsminer2mqtt`

<br>

**Docker via `docker run`**

Example `docker run` command with all environment variables:
```
docker run --name whatsminer2mqtt \
-e MQTT_HOST=10.0.0.2 \
-e MQTT_PORT=1883 \
-e MQTT_USER=user \
-e MQTT_PASSWORD=password \
-e BASE_TOPIC=whatsminer2mqtt \
-e HOMEASSISTANT=True \
-e MINER_IP=10.0.1.4 \
-e INTERVAL=10 \
-e LOG_LEVEL=debug \
tediore/whatsminer2mqtt:latest
```

<br>

**Bare metal (not recommended)**
1. Set the necessary environment variables
2. `git clone https://github.com/Tediore/whatsminer2mqtt`
3. `cd whatsminer2mqtt`
4. `python3 whatsminer2mqtt.py`

<br>

# Configuration
| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `MQTT_HOST` | None | True | IP address or hostname of the MQTT broker to connect to. |
| `MQTT_PORT` | 1883 | True | The port the MQTT broker is bound to. |
| `MQTT_USER` | None | False | The user to send to the MQTT broker. |
| `MQTT_PASSWORD` | None | False | The password to send to the MQTT broker. |
| `BASE_TOPIC` | whatsminer | True | The topic prefix to use for all payloads. |
| `HOME_ASSISTANT` | True | False | Set to `True` to enable Home Assistant MQTT discovery or `False` to disable. |
| `MINER_IP` | None | True | IP address of the Whatsminer API. |
| `INTERVAL` | 10 | True | Interval (in seconds) to query the Whatsminer API and publish MQTT payloads. |
| `LOG_LEVEL` | info | False | Set minimum log level. Valid options are `debug`, `info`, `warning`, and `error` |

<br>

# Home Assistant
whatsminer2mqtt supports Home Assistant MQTT discovery which creates a Device for the Whatsminer instance and entities for each piece of information from the Whatsminer API `summary` command.

<br>

# MQTT topic structure
Payloads for each piece of information are published to `BASE_TOPIC/info/PARAMETER` where `BASE_TOPIC` is the base topic you define and `PARAMETER` is the name of each monitored condition from the `summary` command.

<br>
<a href="https://www.buymeacoffee.com/tediore" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>