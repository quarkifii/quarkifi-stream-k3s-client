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

import json, tarfile
from datetime import datetime, timezone
from kubernetes.client.exceptions import ApiException
import random
import string

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]: {message}")

    
def genearte_random_string(length: int = 10):
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    random_string = ''.join(random.choices(characters, k=length))
    return random_string

def format_k3s_api_error(ex: ApiException):
    # capture the error details and notify the client
    body = json.loads(ex.body) or dict()
    status = ex.status or ""
    reason = ex.reason or ""
    message = body.get("message")
    error = f"status: {status}, reason: {reason}, message: {message}"    
    return error

def get_image_name_and_tag(tar_path):
    with tarfile.open(tar_path, 'r') as tar:
        manifest = tar.extractfile('manifest.json')
        if manifest:
            manifest_data = json.load(manifest)
            repo_tags = manifest_data[0].get('RepoTags', [])
            repo_tag = repo_tags[0]
            image_name, tag = repo_tag.split(":", 1)
            return image_name, tag
        else:
            raise FileNotFoundError("manifest.json not found in tar archive")
            
def format_uptime(start_time):
    now = datetime.now(timezone.utc)
    delta = now - start_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    result = ""
    if days > 0:
        result = f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        result = f"{hours}h {minutes}m"
    elif minutes > 0:
        result = f"{minutes}m {seconds}s"
    else:
        result = f"{seconds}s"
    return result            