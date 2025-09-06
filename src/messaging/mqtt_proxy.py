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

import os, json
from typing import Dict, Any
from utils.logger import get_logger

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class MQTTProxy:
  def __init__(self, upstream_topic: str):
    self._upstream_topic = upstream_topic
    self._mqtt_client = None
    
  def set_client(self, mqtt_client):
    self._mqtt_client = mqtt_client
    
  def notify_message(self, data: Dict[str, Any]):
    try:
        if self._mqtt_client is not None:
            self._mqtt_client.publish(self._upstream_topic, json.dumps(data))
    except Exception as ex:
        logger.error(ex)
        pass