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

import os, threading
from typing import Callable
from utils.logger import get_logger

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class HeartBeat:
    def __init__(self, heartbeat_frequency: int, on_heartbeat_callback: Callable):
        self._heartbeat_frequency = heartbeat_frequency
        self._on_heartbeat_callback = on_heartbeat_callback
        self._stop_event = threading.Event()
        self._reporter_thread = None
    
    def start(self):
        if not self._reporter_thread or not self._reporter_thread.is_alive():
            self._stop_event.clear()
            self._reporter_thread = threading.Thread(target=self._report_status, daemon=True)
            self._reporter_thread.start()
    
    def stop(self):
        self._stop_event.set()
        if self._reporter_thread:
            self._reporter_thread.join(timeout=5)
    
    def _report_status(self):
        while not self._stop_event.is_set():
            try:
                self._stop_event.wait(self._heartbeat_frequency)
                if not self._stop_event.is_set():
                    self._on_heartbeat_callback()
            except Exception as ex:
                logger.error(f"Error reporting status: {ex}")