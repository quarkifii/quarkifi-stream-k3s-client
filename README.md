



## Introduction

[](https://github.com/quarkifii/quarkifi-stream-k3s-client.git)

This repository provides the K3S thin client required to use [Quarkifi Stream](https://qstream.quarkifi.com/) Edge Computing Management.

## What Is Quarkifi Stream Edge Orchestrator Platform
Edge computing is a distributed model that processes data near its source—often on devices like Raspberry Pi or Banana Pi—to minimize latency and bandwidth consumption. Using a platform like [Quarkifi Stream](https://qstream.quarkifi.com/), users can define device endpoints in the cloud and manage applications as containers within a lightweight K3s runtime on the edge devices. This allows for full lifecycle management, including deployment, starting, stopping, and scaling applications remotely.

[Quarkifi Stream](https://qstream.quarkifi.com/) is completely free to start. It provides free access to all Edge Application Management functions for a significant amount of time. 
![Quarkifi Stream k3S Thin Client Deployment](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Multicolor-Pastel-Modern-Corporate-Infographic-And-Chart-Presentation.png)

**Benefits:**

-   **Reduced Latency:** Enables real-time processing for applications like autonomous driving.
    
-   **Improved Security:** Minimizes data exposure by limiting transmission across networks.
    
-   **Lower Operational Costs:** Decreases reliance on expensive cloud bandwidth and infrastructure.

## Quarkifi K3S Edge Thin Client

A python library for managing applications deployed in K3S managed by [Quarkifi Stream](https://qstream.quarkifi.com/) 

## Compatible Hardware

* Raspberry Pi Boards
* Banana PI Boards
* Linux Based boards with capacity to run K3S

## Installation
###   Prerequisites
``` 
#Make Sure Your Linux Box is enabled for cgroup
# 1. Open the cmdline.txt file  
sudo nano /boot/cmdline.txt  
  
#2. Add below into THE END of the current line  
cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory  
  
# 3. Save the file and reboot  
sudo reboot 
```
### Python Environment Setup
``` 
#1 Create Python Virtual Environment. If already exists can go to step 2
cd
python3 -m venv myenv
#2 Enable Python Virtual Environment. Replace myenv with other existing python env 
source myenv/bin/activate
#3 Move to installation
``` 

### Installation Using Git
``` 
cd 
git clone https://github.com/quarkifii/quarkifi-stream-k3s-client.git
cd quarkifi-stream-k3s-client
chmod +x ./setup.sh
./setup.sh
``` 
### Post Installation - Device Connection
####Create Device Endpoint at  [Quarkifi Stream App](https://stream.quarkifi.com/) 
1. Create a user in [Quarkifi Stream App](https://stream.quarkifi.com/) 
2. Navigate to Menu Edge Orchestrator

![Edge Orchestrator](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-165146.png)

3. Click on Add Device

![Device Add Button](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162518.png)

4. Add a suitable device name and click Submit

![Add Device Form](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162633.png)

5. This will create a prompt showing the config.ini file contents. This can also be accessed using DeviceActions -> Connection Info menu

![Config.ini file](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162822-1.png)

6. Copy the contents and replace in the file quarkifi-stream-k3s-client/config/config.ini
7. This will create the required credential to contact the Qstream Console and manage the applications
8. Start the quarkifi-stream-k3s-client service
``` 
sudo service quarkifi-stream-k3s-client start
``` 
9. Logs Check
``` 
cd logs
tail -f qstream-k3s-client.log
#if all proper the logs should print 
mqtt_manager.py | INFO | Connected to mqtt.qconsole.quarkifi.com
``` 
10. Once data is received in cloud the Edge Device Management would show the device details as below

![Device Info](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-164613.png)

### Post Device Connection - Manage Applications
[Manage Applications](applications.md)

## More Information

More information of Quarkifi Stream Platform can be found [here](https://qstream.quarkifi.com).

For any issue please reach out to support@quarkifi.com or raise an issue.


## License

This libary is [licensed](LICENSE) under the [MIT Licence](https://en.wikipedia.org/wiki/MIT_License).

For any issue please reach out to support@quarkifi.com or raise an issue
