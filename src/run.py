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

import os
from service.app_svc import AppManager
from service.heart_beat import HeartBeat
from utils.logger import get_logger
from utils.config import AppConfig
from messaging.mqtt_manager import MQTTManager
from messaging.message_processor import MessageProcessor

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class K3SContainerService:
    def __init__(self):
        self.config = None
        self.message_processor = None
        self.mqtt_manager = None
        self.heartbeat = None
    
    def _on_heartbeat(self):
        AppManager.report_apps_and_resources_status()
    
    def _on_connect_to_mqtt(self, client):
        AppManager.set_mqtt_client(client)
        self.message_processor.start()
        self.heartbeat.start()
        logger.info("Listening for the messages... (Ctrl+C to exit)")        

    def _on_message_from_mqtt(self, payload):
        AppManager.process_request(payload)
    
    def initialize(self):
        try:
            self.config = AppConfig()
            AppManager.init(self.config)
            self.message_processor = MessageProcessor(self._on_message_from_mqtt)
            self.mqtt_manager = MQTTManager(self.config, self.message_processor, self._on_connect_to_mqtt)
            self.heartbeat = HeartBeat(self.config.heartbeat_frequency, self._on_heartbeat)
            return True
        except Exception as ex:
            logger.error(f"initialization error: {ex}")
            return False

    def start(self):
        try:
            # Connect to MQTT broaker
            if not self.mqtt_manager.connect():
                logger.error("failed to connect to MQTT broker")
                return 1
            # Start processing the incoming and outgoing the messages
            self.mqtt_manager.loop_forever()
        except KeyboardInterrupt:
            logger.info("shutting down...")
            self.shutdown()
        except Exception as ex:
            logger.error(f"runtime error: {ex}")
            self.shutdown()
            return 1
        return 0
    
    def shutdown(self):
        if self.mqtt_manager:
            self.mqtt_manager.disconnect()
        if self.heartbeat:
            self.heartbeat.stop()
        if self.message_processor:
            self.message_processor.stop()

def main():
    svc = K3SContainerService()
    
    if not svc.initialize():
        return 1
    
    if svc.start() != 0:
        logger.error("Failed to start the service!!!")
        return 1
    
if __name__ == "__main__":
    main()