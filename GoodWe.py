#!/usr/bin/python -tt
from __future__ import absolute_import
from __future__ import print_function
from daemonpy.daemon import Daemon

import configparser
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import paho.mqtt.client as mqtt
import time
import os
import gzip

import GoodWeCommunicator as goodwe

millis = lambda: int(round(time.time() * 1000))


def logging_namer(name):
    return name + ".gz"


def logging_rotator(source, dest):
    with open(source, "rb") as sf:
        data = sf.read()
        with gzip.open(dest, "wb") as df:
            df.write(data)
    os.remove(source)


def logging_setup(level):
    formatter = logging.Formatter('%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s')

    filehandler = logging.handlers.RotatingFileHandler('/var/log/goodwecomm.log', maxBytes=10*1024*1024,
                                                       backupCount=5)
    filehandler.setFormatter(formatter)

    stdouthandler = logging.StreamHandler(sys.stdout)
    stdouthandler.setFormatter(formatter)

    logger = logging.getLogger('main')
    logger.namer = logging_namer
    logger.rotator = logging_rotator
    logger.addHandler(filehandler)
    logger.addHandler(stdouthandler)
    logger.setLevel(logging.DEBUG)

class MyDaemon(Daemon):
    def run(self):
        config = configparser.RawConfigParser()
        config.read('/etc/goodwe/goodwe.conf')

        mqttserver = config.get("mqtt", "server", fallback="localhost")
        mqttport = config.getint("mqtt", "port", fallback=1883)
        mqtttopic = config.get("mqtt", "topic", fallback="goodwe")
        mqttclientid = config.get("mqtt", "clientid", fallback="goodwe-usb")
        mqttusername = config.get("mqtt", "username", fallback="")
        mqttpasswd = config.get("mqtt", "password", fallback=None) 

        loglevel = config.get("inverter", "loglevel")
        interval = config.getint("inverter", "pollinterval")

        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)

        logging_setup(numeric_level)
        logger = logging.getLogger('main')

        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, mqttclientid)
            if mqttusername != "":
                client.username_pw_set(mqttusername, mqttpasswd);
                logging.debug("Set username -%s-, password -%s-", mqttusername, mqttpasswd)
            client.connect(mqttserver,port=mqttport )
            
            client.loop_start()
        except Exception as e:
            logger.error(e)
            return

        logger.info('Connected to MQTT %s:%s', mqttserver, mqttport)

        self.gw = goodwe.GoodWeCommunicator(logger)

        lastUpdate = millis()
        lastCycle = millis()

        while True:
            try:
                self.gw.handle()

                if (millis() - lastUpdate) > interval:

                    inverter = self.gw.getInverter()

                    if inverter.addressConfirmed:

                        combinedtopic = mqtttopic + '/' + inverter.serial

                        if inverter.isOnline:
                            datagram = inverter.toJSON()
                            logger.debug('Publishing telegram to MQTT on channel ' + combinedtopic + '/data')
                            client.publish(combinedtopic + '/data', datagram)
                            logger.debug('Publishing 1 to MQTT on channel ' + combinedtopic + '/online')
                            client.publish(combinedtopic + '/online', 1)
                        else:
                            logger.debug('Publishing 0 to MQTT on channel ' + combinedtopic + '/online')
                            client.publish(combinedtopic + '/online', 0)

                    lastUpdate = millis()

                time.sleep(0.1)

            except Exception as err:
                logger.exception("Error in RUN-loop")
                break

        client.loop_stop()


if __name__ == "__main__":
    daemon = MyDaemon('/var/run/goodwecomm.pid', '/dev/null', '/var/log/goodwe/comm.out', '/var/log/goodwe/comm.err')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'foreground' == sys.argv[1]:
            daemon.run()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
