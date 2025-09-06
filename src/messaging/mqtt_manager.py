# The MIT License (MIT)
#
# Copyright (c) 2024 Quarkifi Technologies Pvt Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, json, ssl
import paho.mqtt.client as mqtt
from utils.logger import get_logger
from messaging.message_processor import MessageProcessor
from utils.config import AppConfig
from typing import Callable

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class MQTTManager:
    def __init__(self, config: AppConfig, message_processor: MessageProcessor, on_connect_callback: Callable):
        self.config = config
        self.message_processor = message_processor
        self.on_connect_callback = on_connect_callback
        self.client = None
        self._connected = False
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error(f"Connection failed: {reason_code}")
            self._connected = False
        else:
            logger.info(f"Connected to {client._host}:{client._port}")
            self._connected = True
            client.subscribe(self.config.downstream_topic)
            #AppManager.set_mqtt_client(client)
            self.on_connect_callback(client)
    
    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        logger.info(f"Disconnected (Code: {reason_code})")
        self._connected = False
        if reason_code != 0:
            logger.warning("Unexpected disconnect! Attempting reconnect...")
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.message_processor.add_message(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as ex:
            logger.error(f"Error handling message: {ex}")
    
    def connect(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv31)
            self.client.username_pw_set(self.config.mqtt_user, self.config.mqtt_pwd)
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            if self.config.mqtt_protocol == "mqtt":
                self.client.connect(self.config.mqtt_host, self.config.mqtt_port, 120)
            elif self.config.mqtt_protocol == "mqtts":
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                self.client.tls_set_context(context)
                self.client.connect(self.config.mqtt_host, self.config.mqtt_port, 120)
            else:
                raise ValueError(f"Unsupported MQTT protocol: {self.config.mqtt_protocol}")
            
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.disconnect()
    
    def loop_forever(self):
        if self.client:
            self.client.loop_forever()
    
    @property
    def is_connected(self):
        return self._connected