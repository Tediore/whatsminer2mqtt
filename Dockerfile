FROM python:3.9-slim-buster

ADD whatsminer2mqtt.py /

RUN pip install paho.mqtt whatsminer

CMD [ "python", "./whatsminer2mqtt.py" ]