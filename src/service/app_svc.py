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

from service.k3s_helper import K3sHelper
from kubernetes.client.exceptions import ApiException
import os, sys, json, time, re, yaml, psutil, subprocess, traceback
import configparser, requests
from collections import Counter
from utils.commons import genearte_random_string, format_k3s_api_error
from jsonschema import validate, ValidationError
from utils.logger import get_logger
from utils.config import AppConfig
from messaging.task_status_reporter import TaskStatusReporter
from messaging.mqtt_proxy import MQTTProxy

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class AppManager:
    
    _config = None
    _mqtt_proxy = None
    _task_status_reporter = None
    
    @classmethod
    def init(cls, config):
        cls._config = config
        cls._mqtt_proxy = MQTTProxy(config.upstream_topic)
        cls._task_status_reporter = TaskStatusReporter(cls._mqtt_proxy)
    
    @classmethod
    def set_mqtt_client(cls, mqtt_client):
        cls._mqtt_proxy.set_client(mqtt_client)

    @classmethod
    def notify_message(cls, data):
       cls._mqtt_proxy.notify_message(data)


    # This function determines the request and call the relevant function to process the request
    @classmethod
    def process_request(cls, payload):
        logger.info(f"Received the payload: {json.dumps(payload)}")
        request_id = payload.get("request_id")
        request = payload.get("request")
        match request:
            case "import_image":
                cls.import_image(payload)
                return
            case "get_imported_images":
                cls.get_imported_images(payload)
                return                
            case "deploy_app":
                cls.deploy_app(payload)
                return
            case "start_app":
                cls.start_app(payload)
                return
            case "stop_app":
                cls.stop_app(payload)
                return
            case "get_app_status":
                cls.get_app_status(payload)
                return
            case "get_apps_and_resources_status":
                cls.get_apps_and_resources_status(payload)
                return 
            case "get_app_status_and_logs":
                cls.get_app_status_and_logs(payload)
                return 
            case "update_app":
                cls.update_app(payload)
                return                
            case "scale_patch_app":
                cls.scale_patch_app(payload)
                return
            case "image_patch_app":
                cls.image_patch_app(payload)
                return                 
            case "delete_app":
                cls.delete_app(payload)
                return
            case "delete_image":
                cls.delete_image(payload)
                return
            case "delete_all_apps_and_images":
                cls.delete_all_apps_and_images(payload)
                return
            case "get_ssh_public_key":
                cls.get_ssh_public_key(payload)
                return
            case "start_reverse_ssh_connection":
                cls.start_reverse_ssh_connection(payload)
                return                
            case "stop_reverse_ssh_connection":
                cls.stop_reverse_ssh_connection(payload)
                return
            case _:
                logger.error(f"unknown comamnd: {command}")
                return

    # This function downloads the specified image file from the file server, import the image into k3s cluster
    @classmethod
    def import_image(cls, payload):
        logger.info(f"Processing the request 'import_image'")
        request = "import_image"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        image_download_url = payload.get("download_url")
        auth_user = payload.get("auth_user")
        auth_password = payload.get("auth_password")
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            random_string = genearte_random_string()
            local_image_file = f"/tmp/{random_string}.tar"
            
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Downloading")

            # start downloading the image file
            logger.info(f"Downloading the image file")
            response = requests.get(image_download_url, auth=(auth_user, auth_password))
            status_code = response.status_code
            if status_code == 200:
                #print(f"writing to {local_image_file}")
                with open(local_image_file, "wb") as f:
                    f.write(response.content)
                logger.info("Image file downloaded successfully.")
            else:
                error = f"failed to downloaded the file!, error code: {status_code}"
                raise RuntimeError(error)

            cls._task_status_reporter.set_task_status(request_id, "Importing")

            k3s = K3sHelper()
            logger.info(f"Importing the image file into k3 cluster")
            k3s.import_image(local_image_file)
            os.remove(local_image_file)

            # stop the status reporting thread
            stop_event.set()
            
            images_list = k3s.get_imported_images()
            cls.notify_message({"request_id":request_id, "request": "import_image", "status": "Completed", "result": images_list})
            logger.info(f"Completed the request 'import_image'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()
                
    # This function gets the list of imported image names
    @classmethod
    def get_imported_images(cls, payload):
        logger.info("Processing the request 'get_imported_images'")
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return        
        try:
            k3s = K3sHelper()
            images_list = k3s.get_imported_images()
            cls.notify_message({"request_id":request_id, "request": "get_imported_images", "status": "Completed", "result": {"images": images_list}})
            logger.info(f"Completed the request 'get_imported_images'")
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)

    # This function deploys the application
    @classmethod
    def deploy_app(cls, payload):
        logger.info(f"Processing the request 'deploy_app'")
        request = "deploy_app"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            deployment_definition = payload.get("deployment_definition")
            if deployment_definition is None:
                error = "deployment_definition is not specified in the request!"
                raise RuntimeError(error)

            deployment_schema_file = os.path.join(cls._config.home_dir, 'deployment', 'create_deployment_schema.json')
            
            # load the deployment schema
            with open(deployment_schema_file, "r") as file:
                deployment_schema = json.load(file)

            # validate the deployment definition
            try:
                validate(instance=deployment_definition, schema=deployment_schema)
            except ValidationError as ex:
                error = f"create deployment validation has failed, {ex.message}"
                raise RuntimeError(error)

            deployment_name = deployment_definition.get("metadata", {}).get("name")
            namespace = deployment_definition.get("metadata", {}).get("namespace", "default")
            
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Deploying")
            
            k3s = K3sHelper()
            if namespace != "default":
                k3s.create_namespace(namespace)

            # initiate the deployment
            k3s.deploy_app(deployment_definition)
            
            # stop the status reporting thread
            stop_event.set()
            
            app = k3s.get_app_status(deployment_name, namespace)
            # determine the operation status based on app's status
            app_status = app.get("status")
            if app_status == "Healthy":
                status = "Completed"
            else:
                status = "Failed"
            cls.notify_message({"request_id":request_id, "request": "deploy_app", "status": status, "result": app})
            logger.info(f"Completed the request 'deploy_app'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()

    # This function starts the app with the specified image
    @classmethod
    def start_app(cls, payload):
        logger.info("Processing the request 'start_app'")
        request = "start_app"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' not specified in the request")
            return
        app_name = payload.get("app_name")
        if app_name is None:
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": "name is not specified in the request"})
            return

        replicas = payload.get("replicas")
        if (replicas is None) or (not isinstance(replicas, int)) or (replicas <= 0):
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": "replicas is not specified/valid in the request"})
            return
            
        namespace = payload.get("namespace", "default")
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Starting")
            
            k3s = K3sHelper()
            app = k3s.get_app_status(app_name, namespace)
            if app is None:
                error = "application not found in the system"
                raise RuntimeError(error)
            else:
                # Deployment is found. If the app is stopped, then scale it up
                app_status = app.get("status")
                if app_status == "Stopped":
                    k3s.scale_patch_app(app_name, namespace, replicas)
        
            # stop the reporting thread
            stop_event.set()
            
            # get the status of app and report to the client
            app = k3s.get_app_status(app_name, namespace)
            app_status = app.get("status")
            if app_status == "Healthy":
                status = "Completed"
            else:
                status = "Failed"            
            cls.notify_message({"request_id":request_id, "request": request, "status": status, "result": app})
            logger.info(f"Completed the request 'start_app'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()

    # This function stops the specified app
    @classmethod
    def stop_app(cls, payload):
        logger.info(f"Processing the request 'stop_app'")
        request = "stop_app"
        request_id = payload.get("request_id")
        app_name = payload.get("app_name")
        namespace = payload.get("namespace", "default")
        if request_id is None:
            logger.error("'request_id' not specified in the request")
            return
        if app_name is None:
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": "name is not specified in the request"})
            return
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            k3s = K3sHelper()
            app = k3s.get_app_status(app_name, namespace)
            # if the deployment is found and running, the scale down the replicas to 0, to stop it
            if app is not None:
                app_status = app.get("status")
                if app_status != "Stopped":
                    # proceed to stop the app
                    stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Stopping")
                    k3s.scale_patch_app(app_name, namespace, 0)
            else:
                error = "The specified app is not found"
                raise RuntimeError(error)
            
            # stop the reporting thread
            stop_event.set()
            
            # get the status of app and report to the client
            app = k3s.get_app_status(app_name, namespace)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": app})
            logger.info(f"Completed the request 'stop_app'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
           cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()

    # This function gets the specified app's status
    @classmethod
    def get_app_status(cls, payload):
        logger.info(f"Processing the request 'get_app_status'")
        request = "get_app_status"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        app_name = payload.get("app_name")
        namespace = payload.get("namespace", "default")
        if app_name is None:
            error = "app_name is not specified in the request"
            logger.error(error)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            return        
        try:
            k3s = K3sHelper()
            app = k3s.get_app_status(app_name, namespace)
            if app:
                cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": app})
                logger.info(f"Completed the request 'get_app_status'")
            else:
                cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": "specified app not found in the system"})
                logger.error(f"specified app/image is not found in the device")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)

    # This function gets all the apps's status
    @classmethod
    def get_apps_and_resources_status(cls, payload):
        logger.info(f"Processing the request 'apps_and_resources_status'")
        request = "get_apps_and_resources_status"
        request_id = payload.get("request_id")
        try:
            k3s = K3sHelper()
            apps = k3s.get_apps_status()
            resources = cls.get_resources_status()
            apps_status = [app["status"] for app in apps]
            apps_status_counts = Counter(apps_status)
            app_counts = {
                "total": len(apps_status)
            }
            for status, count in apps_status_counts.items():
                app_counts[status] = count
            
            result = {
                "apps": apps,
                "resources": resources,
                "app_counts": app_counts
            }
            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": result})
            logger.info(f"Completed the request '{request}'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)

    # This function updates the spec of the deployed app
    @classmethod
    def update_app(cls, payload):
        logger.info(f"Processing the request 'update_app'")
        request = "update_app"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            deployment_definition = payload.get("deployment_definition")
            if deployment_definition is None:
                error = "deployment_definition is not specified in the request!"
                raise RuntimeError(error)
            
            # load the deployment_schema
            deployment_schema_file = os.path.join(cls._config.home_dir, 'deployment', 'update_deployment_schema.json')
            with open(deployment_schema_file, "r") as file:
                deployment_schema = json.load(file)
            
            # validate the deployment definition
            try:
                validate(instance=deployment_definition, schema=deployment_schema)
            except ValidationError as ex:
                error = f"update deployment schema validation has failed, {ex.message}"
                raise RuntimeError(error)

            deployment_name = deployment_definition.get("metadata").get("name")
            namespace = deployment_definition.get("metadata").get("namespace", "default")
            
            # check whether the deployment exists
            k3s = K3sHelper()
            deployment = k3s.get_deployment(deployment_name, namespace)
            if deployment is None:
                error = "deployment not found!"
                raise RuntimeError(error)
                
            spec = deployment_definition.get("spec")
            
            #delete the 'selector' field if exists
            if spec.get("selector") is not None:
                del spec["selector"]

            if spec.get("template") is not None:
                if spec.get("template").get("metadata") is not None:
                    del spec["template"]["metadata"]
                
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Updating")

            # update the deployment spec
            k3s.update_app(deployment_name, namespace, spec)

            # stop the status reporting thread
            stop_event.set()
            
            app = k3s.get_app_status(deployment_name, namespace)
            # determine the operation status based on app's status
            app_status = app.get("status")
            if app_status == "Healthy":
                status = "Completed"
            else:
                status = "Failed"
            cls.notify_message({"request_id":request_id, "request": request, "status": status, "result": app})
            logger.info(f"Completed the request '{request}'")            
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()

    # This function scales up/down a deployment
    @classmethod
    def scale_patch_app(cls, payload):
        logger.info(f"Processing the request 'scale_patch_app'")
        request = "scale_patch_app"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        
        app_name = payload.get("app_name")
        namespace = payload.get("namespace", "default")
        replicas = payload.get("replicas")
        
        if app_name is None:
            error = "app_name is not specified"
            logger.error(error)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            return        
        
        if (replicas is None) or (not isinstance(replicas, int)) or (replicas < 0):
            error = "replicas is not specified or incorrect value is specified"
            logger.error(error)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            return 
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Patching")

            # patch the scale value to the deployment
            k3s = K3sHelper()   
            k3s.scale_patch_app(app_name, namespace, replicas)
            app = {}
            try:
                app = k3s.get_app_status(app_name, namespace)
            except Exception as ex:
                pass

            # stop the status reporting thread
            stop_event.set()

            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": app})
            logger.info(f"Completed the request 'get_apps_status'")             
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()

    # This function updates the specified image to the deployment
    @classmethod
    def image_patch_app(cls, payload):
        logger.info(f"Processing the request 'image_patch_app'")
        request = "image_patch_app"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        
        app_name = payload.get("app_name")
        namespace = payload.get("namespace", "default")
        container_name = payload.get("container_name")
        new_image = payload.get("new_image")
        image_pull_policy = payload.get("image_pull_policy")
        
        if app_name is None or container_name is None or new_image is None:
            error = "app_name/container_name/new_image is/are not specified!"
            logger.error(error)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            return        
        # initialize event object to control the status reporting thread
        stop_event = None
        
        try:
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Patching")
            
            # patch the scale value to the deployment
            k3s = K3sHelper()
            k3s.image_patch_app(app_name, namespace, container_name, new_image, image_pull_policy)
            app = {}
            try:
                app = k3s.get_app_status(app_name, namespace)
            except Exception as ex:
                pass
                
            # stop the status reporting thread
            stop_event.set()

            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": app})
            logger.info(f"Completed the request 'image_patch_app'")             
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()

    @classmethod
    def get_app_status_and_logs(cls, payload):
        logger.info(f"Processing the request 'get_app_status_and_logs'")
        request = "get_app_status_and_logs"
        # check the necessary parameters are specified in the request
        request_id = payload.get("request_id")
        if request_id is None:
            return
        app_name = payload.get("app_name")
        namespace = payload.get("namespace", "default")
        if app_name is None:
            error = "app_name is not specified in the request"
            logger.error(error)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            return         
        
        tail_n_lines = payload.get("tail_n_lines", 50)
        previous_logs = payload.get("previous_logs", False)

        try:
            k3s = K3sHelper()
            app = k3s.get_app_status_and_logs(app_name, namespace, tail_n_lines, previous_logs)
            if app:
                cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": app})
                logger.info(f"Completed the request 'get_app_status_and_logs'")
            else:
                error = "specified app is not found in the system"
                cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
                logger.error(error)                
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)


    # This function deletes the specified deployment from the system
    @classmethod
    def delete_app(cls, payload):
        logger.info(f"Processing the request 'delete_app'")
        request = "delete_app"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' is not specified in the request")
            return
        app_name = payload.get("app_name")
        namespace = payload.get("namespace", "default")
        if app_name is None:
            error = "app_name is not specified in the request"
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            logger.error(error)
            return    
        try:

            k3s = K3sHelper()
            app = k3s.delete_app(app_name, namespace)
 
            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed"})
            logger.info(f"Completed the request 'delete_app'")
 
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)

    # This function deletes the specified image from the k3s cluster
    @classmethod
    def delete_image(cls, payload):
        logger.info(f"Processing the request 'delete_image'")
        request = "delete_image"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' is not specified in the request")
            return
        image = payload.get("image")
        try:
            k3s = K3sHelper()
            k3s.delete_image(image, False)
            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed"})
            logger.info(f"Completed the request 'delete_image'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)


    # This function deletes the specified deployment from the system
    @classmethod
    def delete_all_apps_and_images(cls, payload):
        logger.info(f"Processing the request 'delete_all_apps_and_images'")
        request = "delete_all_apps_and_images"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' is not specified in the request")
            return        
        
        # event object to control the status reporting thread
        stop_event = None
        
        try:
            stop_event = cls._task_status_reporter.start_reporting(request_id, request, "Deleting")
            
            k3s = K3sHelper()
            k3s.delete_all_apps_and_images()

            # stop the status reporting thread
            stop_event.set()

            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed"})
            logger.info(f"Completed the request '{request}'")
        except ApiException as ex:
            cls._handle_api_error(request_id, request, ex)
        except Exception as ex:
            cls._handle_generic_error(request_id, request, ex)
        finally:
            if stop_event is not None:
                stop_event.set()
                
    @classmethod
    def get_resources_status(cls):
        resources = dict()
        # get cpu usage details
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=True)
        resources["cpu"] = {
            "count": cpu_count,
            "usage_percent": cpu_percent,
        }
    
        # get Memory(RAM) usage details
        mem = psutil.virtual_memory()
        resources["memory"] = {
            "total": mem.total // 1024,
            "used": mem.used // 1024,
            "free": mem.available // 1024,
            "usage_percent": mem.percent
        }
        
        # get swap memory usage details
        swap = psutil.swap_memory()
        resources["swap"] = {
            "total": swap.total // 1024,
            "used": swap.used // 1024,
            "free": swap.free // 1024,
            "usage_percent": swap.percent
        }
        
        # get Disk Usage (for the root partition '/') details
        disk = psutil.disk_usage('/')
        resources["disk"] = {
            "total": disk.total // 1024,
            "used": disk.used // 1024,
            "free": disk.free // 1024,
            "usage_percent": disk.percent
        }     
        return resources


    # This function is called periodically in a timer thread, keeps reporting all the apps' status with CPU and Memory usage metrics
    @classmethod
    def report_apps_and_resources_status(cls):
        logger.info(f"Processing 'report_apps_and_resources_status'")
        try:
            k3s = K3sHelper()
            apps = k3s.get_apps_status()
            resources = cls.get_resources_status()
            apps_status = [app["status"] for app in apps]
            apps_status_counts = Counter(apps_status)
            app_counts = {
                "total": len(apps_status)
            }
            for status, count in apps_status_counts.items():
                app_counts[status] = count
            
            status = {
                "apps": apps,
                "resources": resources,
                "app_counts": app_counts
            }
            cls.notify_message({"status_update":"apps_and_resources_status", "status": status})
        except Exception as ex:
            error = str(ex)
            logger.error(error)

    @classmethod
    def get_ssh_public_key(cls, payload):
        logger.info(f"Processing the request 'get_ssh_public_key'")
        request = "get_ssh_public_key"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' is not specified in the request")
            return
        user_name = payload.get("user_name")
        if user_name is None:
            error = "user_name is not specified in the request"
            cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
            logger.error(error)
            return
        public_key_file = f"/home/{user_name}/.ssh/qstream.pub"
        try:
            with open(public_key_file, 'r') as file:
                content = file.read()
                content = content.rstrip("\n")
            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": {"public_key": content}})
        except Exception as ex:
            logger.error(str(ex))
            cls._handle_generic_error(request_id, request, ex)

    @classmethod
    def start_reverse_ssh_connection(cls, payload):
        logger.info(f"Processing the request 'start_reverse_ssh_connection'")
        request = "start_reverse_ssh_connection"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' is not specified in the request")
            return
        service_name = 'quarkifi-stream-ssh-tunnel'
        try:
            ssh_bridge_server = payload.get("ssh_bridge_server")
            if ssh_bridge_server is None:
                error = "ssh_bridge_server is not specified in the request"
                cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "reason": error})
                logger.error(error)
                return
            file_path = f"/tmp/{service_name}.env"
            text_line = f"SSH_BRIDGE_SERVER={ssh_bridge_server}"
            with open(file_path, 'w') as file:
                file.write(text_line + '\n')

            request_start_time = int(time.time())

            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', service_name],
                capture_output=True,
                text=True,
                check=True
            )

            result = subprocess.run(
                ['sudo', 'systemctl', 'start', service_name],
                capture_output=True,
                text=True,
                check=True
            )

            log_file = "/tmp/quarkifi-stream-ssh-tunnel.log"
            log_file_updated = False
            count = 0
            allocated_port = None
            while True:
                time.sleep(1)
                count += 1
                if os.path.exists(log_file):
                    log_file_updated_time = int(os.path.getmtime(log_file))
                    logger.info(f"request_start_time: {request_start_time}, log_file_updated_time: {log_file_updated_time}")
                    log_file_updated = os.path.exists(log_file) and (log_file_updated_time >= request_start_time)
                    if (log_file_updated == True) or (count >= 10):
                        time.sleep(1)
                        break

            content = ""
            if log_file_updated:
                time.sleep(1)
                with open(log_file, 'r') as file:
                    content = file.read()
                    match = re.search(r'Allocated port (\d+)', content)
                    allocated_port = int(match.group(1)) if match else None

            if log_file_updated and allocated_port:
                logger.info(f"Successfully started the ssh tunnel!")
                result = {
                    "allocated_port": allocated_port
                }
                cls.notify_message({"request_id":request_id, "request": request, "status": "Completed", "result": result})
            else:
                logger.info(f"Failed to start the ssh tunnel!")
                cls.notify_message({"request_id":request_id, "request": request, "status": "Failed", "error": content})
        except subprocess.CalledProcessError as ex:
            logger.error(f"Failed to start the service {service_name}: {ex.stderr}")
            cls._handle_generic_error(request_id, request, ex)

    @classmethod
    def stop_reverse_ssh_connection(cls, payload):
        logger.info(f"Processing the request 'stop_reverse_ssh_connection'")
        request = "stop_reverse_ssh_connection"
        request_id = payload.get("request_id")
        if request_id is None:
            logger.error("'request_id' is not specified in the request")
            return
        service_name = 'quarkifi-stream-ssh-tunnel'
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', service_name],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Successfully stopped the {service_name} service")
            cls.notify_message({"request_id":request_id, "request": request, "status": "Completed"})
        except subprocess.CalledProcessError as ex:
            logger.error(f"Failed to stop the service {service_name}: {ex.stderr}")
            cls._handle_generic_error(request_id, request, ex)

    @classmethod
    def _handle_error(cls, request_id: str, request: str, error: str):
        logger.error(f"request: {request}, request_id: {request_id}, error: {error}")
        cls._mqtt_proxy.notify_message({
            "request_id": request_id, 
            "request": request, 
            "status": "Failed", 
            "reason": error
        })
    
    @classmethod
    def _handle_api_error(cls, request_id: str, request: str, ex: ApiException):
        error = format_k3s_api_error(ex)
        cls._handle_error(request_id, request, error)
    
    @classmethod
    def _handle_generic_error(cls, request_id: str, request: str, ex: Exception):
        error = str(ex)
        cls._handle_error(request_id, request, error)            
