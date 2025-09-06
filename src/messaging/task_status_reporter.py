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

from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Dict, Any, Optional
from messaging.mqtt_proxy import MQTTProxy

class TaskStatusReporter:

    _mqtt_proxy = None
    _task_status: Dict[str, str] = None
    _executor = None
    
    def __init__(self, mqtt_proxy: MQTTProxy):
        self._mqtt_proxy = mqtt_proxy
        self._task_status: Dict[str, str] = {}
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="app-pool")

    def set_task_status(self, request_id: str, status: str):
        self._task_status[request_id] = status
    
    def get_task_status(self, request_id: str) -> Optional[str]:
        return self._task_status.get(request_id)
    
    def start_reporting(self, request_id: str, request: str, status: str) -> threading.Event:
        self._task_status[request_id] = status
        stop_event = threading.Event()
        self._executor.submit(self._report_task_status_thread, stop_event, request_id, request)
        return stop_event
    
    def _report_task_status_thread(self, stop_event: threading.Event, request_id: str, request: str):
        while not stop_event.is_set():
            status = self._task_status.get(request_id)
            if status is not None:
                message = {
                    "request_id": request_id, 
                    "request": request,
                    "status": status
                }
                self._mqtt_proxy.notify_message(message)
            stop_event.wait(2)