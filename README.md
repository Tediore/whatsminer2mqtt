WIP

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
    - MQTT_KEEPALIVE=300
    - MQTT_QOS=1
    - BASE_TOPIC=whatsminer2mqtt
    - MINER_IP=10.0.1.4
    - MINER_TOKEN=a1b2c3d4e5
    - INTERVAL=30
    - LOG_LEVEL=debug
    restart: unless-stopped
```