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

import os, re, threading, subprocess, tempfile, shutil, json, psutil
from kubernetes import client, config
from kubernetes.client import V1Pod
from kubernetes.client.exceptions import ApiException
from typing import List, Dict, Optional
from utils.commons import format_uptime
from datetime import datetime
from utils.logger import get_logger

current_file = os.path.basename(__file__)
logger = get_logger(current_file)

class K3sHelper:
    def __init__(self):
        try:
            config.load_kube_config("/etc/rancher/k3s/k3s.yaml")
            self.core_api = client.CoreV1Api()
        except Exception as e:
            raise RuntimeError(f"Failed to load kubeconfig: {str(e)}")
    
    def extract_appname_and_imagename(self, imagepath):
        start_index = imagepath.rindex("/") + 1
        image_name = imagepath[start_index:]
        app_name, _ = image_name.split(":", 1)
        return app_name, image_name
    
    def parse_quantity(self, quantity_str: str):
        #Parse Kubernetes quantity strings (CPU/memory) into numeric values
        if quantity_str.endswith('n'):  # nanocores
            return float(quantity_str[:-1]) / 1_000_000  # to millicores
        elif quantity_str.endswith('m'):  # millicores
            return float(quantity_str[:-1])
        elif quantity_str.endswith('Ki'):  # kibibytes
            return float(quantity_str[:-2]) / 1024  # to MiB
        elif quantity_str.endswith('Mi'):  # mebibytes
            return float(quantity_str[:-2])
        elif quantity_str.endswith('Gi'):  # gibibytes
            return float(quantity_str[:-2]) * 1024  # to MiB
        else:  # assume bytes (no suffix)
            return float(quantity_str) / (1024 * 1024)  # bytes to MiB
    
    def get_system_boot_time(self):
        """get system boot time as UTC datetime"""
        boot_timestamp = psutil.boot_time()
        return datetime.utcfromtimestamp(boot_timestamp)
    
    # This function is to import the specified image into the k3s cluster
    def import_image(self, image_file: str) -> None:
        result = subprocess.run(
            ['sudo', 'k3s', 'ctr', 'images', 'import', image_file],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if(result.returncode != 0):
            log_line = result.stderr
            error = log_line
            match = re.search(r'msg="([^"]+)"', log_line)
            if match:
                error = match.group(1)
            raise RuntimeError(error)        

    def get_imported_images(self):
        #get list of all images imported into k3s cluster
        result = subprocess.run(
            ['sudo', 'k3s', 'ctr', 'images', 'list', '-q'],
            capture_output=True,
            text=True,
            check=True
        )
        result = result.stdout.strip().split('\n') if result.stdout else []
        images_list = []
        for image_path in result:
            if(not image_path.startswith("docker.io/rancher") and not image_path.startswith("sha")):
                start_index = image_path.rindex("/") + 1
                image = image_path[start_index:]
                images_list.append(image)
        return images_list

    # create namespace
    def create_namespace(self, namespace: str):
        try:
            core_v1_api = client.CoreV1Api()
            core_v1_api.read_namespace(name=namespace)
        except ApiException as e:
            if e.status == 404:
                ns_body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
                core_v1_api.create_namespace(ns_body)
            else:
                raise
        
        
    def deploy_app(self, deployment_yaml: str):
        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()
        api_client = client.ApiClient()
        
        app_name = deployment_yaml.get("metadata").get("name")
        namespace = deployment_yaml.get("metadata").get("namespace", "default")
        deployment_obj = api_client._ApiClient__deserialize(deployment_yaml, client.V1Deployment)
        
        # check the images with imagePullPolicy "Never" are available in local repo
        containers = deployment_obj.spec.template.spec.containers
        images = []
        for container in containers:
            image = container.image
            image_pull_policy = container.image_pull_policy
            if image_pull_policy == "Never":
                images.append(image)
        imported_images = self.get_imported_images()
        if images and not set(images).issubset(imported_images):
            error = "image(s) specified in the deployment definition is not found in the system!"
            raise RuntimeError(error)
        
        # Create deployment
        apps_v1_api.create_namespaced_deployment(namespace=namespace, body=deployment_obj)

        # wait for the deployment to reach 'healthy' state
        wait_event = threading.Event()
        wait_event.wait(5)
        for _ in range(120):
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
            if deployment is not None:
                spec = deployment.spec
                status = deployment.status
                desired = spec.replicas or 0
                available = status.available_replicas or 0
                updated = status.updated_replicas or 0
                unavailable = status.unavailable_replicas or 0
                # wait if deployment is not 'healthy' yet
                if not (available == desired and updated == desired):
                    wait_event.wait(1)
                else:
                    break
    
    def get_deployment(self, app_name: str, namespace: str):
        apps_v1_api = client.AppsV1Api()
        deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
        return deployment

    def update_app(self, app_name: str, namespace: str, spec: dict):
        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()
        
        spec_patch = {
            "spec": spec
        }
        
        apps_v1_api.patch_namespaced_deployment(
            name=app_name,
            namespace=namespace,
            body=spec_patch
        )

        # wait for the deployment to reach the desired state
        wait_event = threading.Event()
        wait_event.wait(5)
        for _ in range(120):
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
            if deployment is not None:
                spec = deployment.spec
                status = deployment.status
                desired = spec.replicas or 0
                available = status.available_replicas or 0
                updated = status.updated_replicas or 0
                unavailable = status.unavailable_replicas or 0
                # wait if deployment is not 'healthy' yet
                if not (available == desired and updated == desired):
                    wait_event.wait(1)
                else:
                    break       
        
    def scale_patch_app(self, app_name: str, namespace: str, replicas: int):
        scale_patch = {
            "spec": {
                "replicas": replicas
            }
        }
        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()
        
        apps_v1_api.patch_namespaced_deployment(
            name=app_name,
            namespace=namespace,
            body=scale_patch
        )

        # wait for the deployment to reach the desired state
        wait_event = threading.Event()
        wait_event.wait(5)
        for _ in range(120):
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
            if deployment is not None:
                try:
                    if replicas == 0: # case of stop app
                        label_selector = ",".join([f"{k}={v}" for k, v in deployment.spec.selector.match_labels.items()])
                        pods = core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector).items
                        # wait till all pods are deleted for the app
                        if len(pods) > 0:
                            wait_event.wait(1)
                        else:
                            break
                    else: # case of start app or scale up
                        label_selector = ",".join([f"{k}={v}" for k, v in deployment.spec.selector.match_labels.items()])
                        pods = core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector).items
                        statuses = [pod.status.phase for pod in pods]
                        # wait for all pods to reach 'Running' state
                        if all(status == 'Running' for status in statuses):
                            break
                        else:
                            wait_event.wait(1)
                except Exception as ex:
                    wait_event.wait(1)


    def image_patch_app(self, app_name: str, namespace: str, container_name: str, new_image: str, image_Pull_policy: str):
        apps_v1_api = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()
        
        if image_Pull_policy is None:
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
            for container in deployment.spec.template.spec.containers:
                if container_name == container.name:
                    image_Pull_policy = container.image_pull_policy
        
        container = {
            "name": container_name,
            "image": new_image,
            "imagePullPolicy": image_Pull_policy
        }

        image_patch = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            container
                        ]
                    }
                }
            }
        }

        apps_v1_api.patch_namespaced_deployment(
            name=app_name,
            namespace=namespace,
            body=image_patch
        )

        # wait for the image patch is complete
        wait_event = threading.Event()
        wait_event.wait(5)
        for _ in range(120):
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
            label_selector = ",".join([f"{k}={v}" for k, v in deployment.spec.selector.match_labels.items()])
            pods = core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector).items
            # check all targetted containers are updated with new image
            all_updated = True
            for pod in pods:
                for container in pod.spec.containers:
                    if container.name == container_name and container.image != new_image:
                        all_updated = False
                        break
            # if not all the targetted containers are not updated with new image, then wait for a sec and check again
            if not all_updated:
                wait_event.wait(1)
            else:
                break

        
    def get_app_status(self, app_name: str, namespace: str="dafault"):
        core_v1_api = client.CoreV1Api()
        apps_v1_api = client.AppsV1Api()
        metrics_api = client.CustomObjectsApi()
        try:
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
        except Exception as ex:
            return None
        if deployment:

            spec = deployment.spec
            status = deployment.status
            desired_replicas = spec.replicas or 0
            available_replicas = status.available_replicas or 0
            updated_replicas = status.updated_replicas or 0
            unavailable_replicas = status.unavailable_replicas or 0

            app_uptime = None
            app = None
            pods_ = []

            match_labels = deployment.spec.selector.match_labels
            label_selector = ",".join([f"{k}={v}" for k, v in match_labels.items()])
            pods = core_v1_api.list_namespaced_pod(namespace=namespace, label_selector=label_selector).items
            statuses = [pod.status.phase for pod in pods]

            app_status = "Unknown"
            if desired_replicas == 0 and len(pods) == 0:
                app_status = "Stopped"
            elif desired_replicas > 0 and desired_replicas == len(pods):
                # if all pods are 'Running', then app is 'Healthy'
                if all(status == 'Running' for status in statuses):
                    app_status = "Healthy"
                # if all pods are 'Pending', then app is 'Pending'
                elif all(status == 'Pending' for status in statuses):
                    app_status = "Pending"
                elif any(status == 'Running' for status in statuses):
                    app_status = "Partial"
            elif desired_replicas == 0 and len(pods) > 0:
                app_status = "Stopping"

            total_cpu_usage = 0
            total_memory_usage = 0
            pod_count = 0

            for pod in pods:
                pod_name = pod.metadata.name
                containers = []
                
                # Get pod metrics for CPU and memory usage
                try:
                    pod_metrics = metrics_api.get_namespaced_custom_object(
                        group="metrics.k8s.io",
                        version="v1beta1", 
                        namespace=namespace,
                        plural="pods",
                        name=pod_name
                    )
                    
                    pod_cpu_usage = 0
                    pod_memory_usage = 0
                    
                    for container_metric in pod_metrics.get('containers', []):
                        # Parse CPU usage (e.g., "1500m" -> 1.5 cores)
                        cpu_str = container_metric.get('usage', {}).get('cpu', '0')
                        if cpu_str.endswith('m'):
                            pod_cpu_usage += int(cpu_str[:-1]) / 1000
                        elif cpu_str.endswith('n'):
                            pod_cpu_usage += int(cpu_str[:-1]) / 1000000000
                        else:
                            pod_cpu_usage += float(cpu_str)
                        
                        # Parse memory usage (e.g., "128Mi" -> bytes)
                        memory_str = container_metric.get('usage', {}).get('memory', '0')
                        if memory_str.endswith('Ki'):
                            pod_memory_usage += int(memory_str[:-2]) * 1024
                        elif memory_str.endswith('Mi'):
                            pod_memory_usage += int(memory_str[:-2]) * 1024 * 1024
                        elif memory_str.endswith('Gi'):
                            pod_memory_usage += int(memory_str[:-2]) * 1024 * 1024 * 1024
                        else:
                            pod_memory_usage += int(memory_str)
                    
                    total_cpu_usage += pod_cpu_usage
                    total_memory_usage += pod_memory_usage
                    pod_count += 1
                    
                except Exception:
                    # If metrics are not available, skip this pod
                    pass
                
                for container in pod.spec.containers:
                    containers.append({"name": container.name, "image": container.image})
                pods_.append({"name": pod_name, "status":pod.status.phase, "containers": containers})
                namespace = pod.metadata.namespace
                status = pod.status.phase
                start_time = pod.status.start_time
                if start_time is not None:
                    # get system boot time to handle reboot scenarios
                    boot_time = self.get_system_boot_time()
                    pod_start_time = start_time.replace(tzinfo=None)
                    # Use the later of boot time or pod start time as the effective start time
                    effective_start_time = max(boot_time, pod_start_time)
                    pod_uptime = int((datetime.utcnow() - effective_start_time).total_seconds())

                    # capture the earliest uptime time among the pods
                    if app_uptime is None:
                        app_uptime = pod_uptime
                    else:
                        if pod_uptime > app_uptime:
                            app_uptime = pod_uptime

            # Get total CPU and memory requests for baseline calculation
            total_cpu_requests = 0
            total_memory_requests = 0
            
            for pod in pods:
                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        # Parse CPU requests
                        cpu_request = container.resources.requests.get('cpu', '0')
                        if cpu_request.endswith('m'):
                            total_cpu_requests += int(cpu_request[:-1]) / 1000
                        elif cpu_request.endswith('n'):
                            total_cpu_requests += int(cpu_request[:-1]) / 1000000000
                        else:
                            total_cpu_requests += float(cpu_request) if cpu_request != '0' else 0
                        
                        # Parse memory requests
                        memory_request = container.resources.requests.get('memory', '0')
                        if memory_request.endswith('Ki'):
                            total_memory_requests += int(memory_request[:-2]) * 1024
                        elif memory_request.endswith('Mi'):
                            total_memory_requests += int(memory_request[:-2]) * 1024 * 1024
                        elif memory_request.endswith('Gi'):
                            total_memory_requests += int(memory_request[:-2]) * 1024 * 1024 * 1024
                        else:
                            total_memory_requests += int(memory_request) if memory_request != '0' else 0
            
            # Calculate CPU usage percentage
            # If no CPU requests are defined, use pod_count as baseline (1 core per pod)
            cpu_baseline = total_cpu_requests if total_cpu_requests > 0 else pod_count
            cpu_usage_percentage = round((total_cpu_usage / cpu_baseline * 100), 2) if pod_count > 0 and cpu_baseline > 0 else 0
            
            # Calculate memory usage percentage
            # If no memory requests are defined, use system memory as baseline
            virtual_memory_total = psutil.virtual_memory().total
            memory_baseline = total_memory_requests if total_memory_requests > 0 else virtual_memory_total
            memory_usage_percentage = round((total_memory_usage / memory_baseline * 100), 2) if pod_count > 0 and memory_baseline > 0 else 0

            app = {
                "app_name": app_name,
                "namespace": namespace,
                "status": app_status,
                "pods": pods_,
                "replicas": {
                  "desired": desired_replicas,
                  "available": available_replicas,
                  "updated": updated_replicas,
                  "unavailable": unavailable_replicas
                },
                "cpu_usage": cpu_usage_percentage,
                "mem_usage": memory_usage_percentage,
            }
            if app_uptime is not None:
                app["uptime"] = app_uptime
            return app
        else:
            return None

        
    def get_app_status_and_logs(self, app_name: str, namespace: str, tail_n_lines, previous_logs:bool):
        # create API clients
        app = self.get_app_status(app_name, namespace)
        if app:
            core_v1_api = client.CoreV1Api()
            apps_v1_api = client.AppsV1Api()
            deployment = apps_v1_api.read_namespaced_deployment(app_name, namespace)
            selector = deployment.spec.selector.match_labels
            label_selector = ",".join(f"{k}={v}" for k, v in selector.items())
            pods = core_v1_api.list_namespaced_pod(namespace, label_selector=label_selector)
            logs = []
            for pod in pods.items:
                pod_name = pod.metadata.name
                lines = []
                for container in pod.spec.containers:
                    container_name = container.name
                    try:
                        log_string = core_v1_api.read_namespaced_pod_log(
                                        name=pod_name,
                                        namespace=namespace,
                                        container=container_name,
                                        tail_lines=tail_n_lines,
                                        previous = previous_logs
                                    )
                        lines = log_string.split('\n')
                        lines = [line for line in lines if line]
                    except Exception as ex:
                        # ignore, exception will be thrown if previous container is not found
                        pass
                    logs.append({
                        "pod": pod_name,
                        "container": container_name,
                        "logs": lines
                    })

            app["logs"] = logs
            return app
        else:
            raise RuntimeError("app not found")
        
    # This function gets the status of all the deployments/apps
    def get_apps_status(self):
        apps_v1_api = client.AppsV1Api()
        # fetch deployments in all namespaces
        deployments = apps_v1_api.list_deployment_for_all_namespaces()
        apps = []
        for deployment in deployments.items:
            name = deployment.metadata.name
            namespace = deployment.metadata.namespace
            if namespace != 'kube-system':
                app = self.get_app_status(name, namespace)
                apps.append(app)
        return apps

    # This function deletes the specified deployment/app from the k3s cluster
    def delete_app(self, app_name: str, namespace: str = "default"):
        apps_v1_api = client.AppsV1Api()
        apps_v1_api.delete_namespaced_deployment(
            name=app_name,
            namespace=namespace,
            body=client.V1DeleteOptions()
        )
        # wait for the deployment to get deleted
        wait_event = threading.Event()
        for _ in range(60):
            try:
                apps_v1_api.read_namespaced_deployment(app_name, namespace)
            except ApiException as ex:
                # check if the deployment is deleted
                if ex.status == 404:
                    break
            wait_event.wait(1)

    # This function deletes the specified image from the k3s cluster
    def delete_image(self, target_image: str, force: bool = False) -> None:
        apps_v1_api = client.AppsV1Api()
        if force == False:
            logger.info("delete_image, checking whether any apps using the image")
            deployments = apps_v1_api.list_deployment_for_all_namespaces()
            images_in_use = set()
            for deployment in deployments.items:
                for container in deployment.spec.template.spec.containers:
                    images_in_use.add(container.image)

            if target_image in images_in_use:
                raise RuntimeError("The specified image is in use!")

        result = subprocess.run(
            ['sudo', 'crictl', 'rmi', target_image],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if(result.returncode != 0):
            log_line = result.stderr
            error = log_line
            match = re.search(r'msg="([^"]+)"', log_line)
            if match:
                error = match.group(1)
            raise RuntimeError(error)

    # This function deletes all the deployed apps and imported images from the system
    def delete_all_apps_and_images(self):
        apps_v1_api = client.AppsV1Api()
        deployments = apps_v1_api.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            app_name = deployment.metadata.name
            namespace = deployment.metadata.namespace
            if namespace != 'kube-system':
                try:
                    self.delete_app(app_name, namespace)
                except Exception as ex:
                    pass
            
        images = self.get_imported_images()
        for image in images:
            try:
                self.delete_image(image, True)
            except Exception as ex:
                pass