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

import os, threading, queue
from utils.logger import get_logger
from typing import Callable

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class MessageProcessor:
    def __init__(self, on_message_callback: Callable):
        self.message_queue = queue.Queue()
        self.on_message_callback = on_message_callback
        self._running = False
        self._worker_thread = None

    def add_message(self, payload):
        self.message_queue.put(payload)

    def start(self):
        if not self._running:
            self._running = True
            self._worker_thread = threading.Thread(target=self._process_messages, daemon=True)
            self._worker_thread.start()

    def stop(self):
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

    def _process_messages(self):
        while self._running:
            try:
                payload = self.message_queue.get(timeout=1)
                self.on_message_callback(payload)
            except queue.Empty:
                continue
            except Exception as ex:
                logger.error(f"Error processing message: {ex}")