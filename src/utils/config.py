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
import configparser
from typing import Optional
from utils.logger import get_logger

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class AppConfig:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        self._config = configparser.ConfigParser()
        self._home_dir = os.getenv("K3S_THIN_CLIENT_HOME")
        
        if self._home_dir is None:
            logger.error("Error: environment variable K3S_THIN_CLIENT_HOME is not set!")
            raise RuntimeError("K3S_THIN_CLIENT_HOME environment variable not set")
        
        self.config_file = os.path.join(self._home_dir, 'config', 'config.ini')
       
        if not os.path.exists(self.config_file):
            logger.error(f"Configuration file not found: {self.config_file}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        self._config.read(self.config_file)
        logger.info(f"Configuration loaded")

    @property
    def home_dir(self) -> str:
        return self._home_dir
        
    @property
    def heartbeat_frequency(self) -> int:
        return int(self._config.get("general", "heartbeat_frequency"))
    
    @property
    def mqtt_host(self) -> str:
        return self._config.get("mqtt", "host")
    
    @property
    def mqtt_port(self) -> int:
        return int(self._config.get("mqtt", "port"))
    
    @property
    def mqtt_protocol(self) -> str:
        return self._config.get("mqtt", "protocol")
    
    @property
    def mqtt_user(self) -> str:
        return self._config.get("mqtt", "user")
    
    @property
    def mqtt_pwd(self) -> str:
        return self._config.get("mqtt", "password")
    
    @property
    def mqtt_device_key(self) -> str:
        return self._config.get("mqtt", "device_key")
    
    @property
    def upstream_topic(self) -> str:
        return f"/{self.mqtt_user}/{self.mqtt_device_key}/upstream_edge_k3s"
    
    @property
    def downstream_topic(self) -> str:
        return f"/{self.mqtt_user}/{self.mqtt_device_key}/downstream_edge_k3s"


def get_app_config() -> AppConfig:
    """Get the singleton AppConfig instance"""
    return AppConfig()