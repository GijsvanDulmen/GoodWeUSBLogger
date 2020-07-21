FROM arm64v8/debian:buster-slim

RUN apt-get update
RUN apt-get install -y python-pip

RUN python -m pip install configparser paho-mqtt pyudev ioctl_opt simplejson enum34

COPY . /app

CMD [ "python", "/app/GoodWe.py", "foreground" ]