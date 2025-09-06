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

# callback function to handle beartbeat
def on_heartbeat():
    AppManager.report_apps_and_resources_status()

# callback function to handle on connect (to mqtt) event
def on_connect_to_mqtt(client):
    AppManager.set_mqtt_client(client)

# callback function to handle message from mqtt    
def on_message_from_mqtt(payload):
    AppManager.process_request(payload)

def main():
    try:
        config = AppConfig()
        AppManager.init(config)
        message_processor = MessageProcessor(on_message_from_mqtt)
        mqtt_manager = MQTTManager(config, message_processor, on_connect_to_mqtt)
        heartbeat = HeartBeat(config.heartbeat_frequency, on_heartbeat)

        if not mqtt_manager.connect():
            logger.error("failed to connect to MQTT broker")
            return 1
        
        message_processor.start()        
        heartbeat.start()
        logger.info("listening for messages... (Ctrl+C to exit)")
        try:
            mqtt_manager.loop_forever()
        except KeyboardInterrupt:
            mqtt_manager.disconnect()
            heartbeat.stop()
            message_processor.stop()

    except Exception as ex:
        logger.error(f"application error: {ex}")
        return 1
    
if __name__ == "__main__":
    main()