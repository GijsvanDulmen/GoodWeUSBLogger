FROM arm64v8/debian:buster-slim

RUN apt-get update
RUN apt-get install -y python-pip libusb-1.0-0

RUN python -m pip install configparser paho-mqtt pyudev ioctl_opt simplejson enum34 pyusb

COPY . /app

CMD [ "python", "/app/GoodWe.py", "foreground" ]