



## Manage Applications
Once the Edge Device is configured you can create applications over the K3S container system remotely managed from Quarkifi Stream. 
To manage Applications from the edge device click on Device Actions-> View Applications

![Edge Applications](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-171003.png)

One can manage two types of applications using Quarkifi Edge Orchestrator for K3S.
		1.Docker Image From Registry
		2.Upload Custom Docker Image

### Create Application Using Docker Image From Registry
1. Click Add to create Application

![Application Add Button](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162518.png)

2. Fillup following details in the application form
	i.	Select Image Type as 'Use Docker Image' to use standard docker image from registry
	ii.	Provide the docker Image Name 
	iii. Provide a user specific app version
	iv. Provide a user friendly name to identify the application
	v.  One can create multiple instance by setting the no of replicas
	vi. One can setup optional volume and other container options in Advance Options

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-171624.png)

3. Click on Deploy to deploy the new application.
	i.  It may take some time to make the application ready.
	ii. Please wait till the processing of the deployment is over
![Processing Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174131.png)

4. Once Deploy you should be able to see the running state of the application
![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174425.png)

5. Once deployed click on App Actions -> Show Logs
	This will show the application logs.
	The application is now ready and in running state if the logs are fine an as expected
	
![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174631.png)
6. Click on Deploy to deploy the new application.
	i.  It may take some time to make the application ready.
	ii. Please wait till the processing of the deployment is over
![Processing Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174131.png)

7. Once Deploy you should be able to see the running state of the application
![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174425.png)

8. Once deployed click on App Actions -> Show Logs
	This will show the application logs.
	The application is now ready and in running state if the logs are fine an as expected
	
![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174631.png)

### Create Application Upload Custom Built Docker Image
##### Build Docker Image for Target Architecture
Example : If you are generating docker image for raspberrypi board you can use below command to generate the .gz file to be used for upload.
``` 
#cmd: sudo docker buildx build --platform linux/arm64 -t log-newimage:v2 --output type=docker,dest=image-processor-pi.tar .
#cmd: gzip image-processor-pi.tar
``` 
This will generate the gz image (e.g image-processor-pi.tar.gz) which can be used to upload to the edge device for deployment as an application

### Create Application Using Image Upload
1. Click Add to create Application

![Application Add Button](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162518.png)

2. Fillup following details in the application form
	i.	Select Image Type as 'Upload Image' to upload image generated locally
	ii.	Click on Select Docker Image

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-181823.png)

3. Once Selected the form will show the selected image

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-182312.png)

4. Upload the selected image

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-184008.png)

5. Once Uploaded it would open a Application Form
	Fillup following details in the application form
	i.	Select Image Type as 'Upload Image' to use uploaded Image
	ii. Provide a user specific app version
	iii. Provide a user friendly name to identify the application
	iv.  One can create multiple instance by setting the no of replicas
	v. One can setup optional volume and other container options in Advance Options

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-184244.png)

6. Click on Deploy to deploy the new application.
	i.  It may take some time to make the application ready.
	ii. Please wait till the processing of the deployment is over
![Processing Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174131.png)

7. Once Deploy you should be able to see the running state of the application
![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174425.png)

8. Once deployed click on App Actions -> Show Logs
	This will show the application logs.
	The application is now ready and in running state if the logs are fine an as expected
	
![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174631.png)

## More Information

More information of Quarkifi Stream Platform can be found [here](https://qstream.quarkifi.com).

For any issue please reach out to support@quarkifi.com or raise an issue.


## License

This libary is [licensed](LICENSE) under the [MIT Licence](https://en.wikipedia.org/wiki/MIT_License).

For any issue please reach out to support@quarkifi.com or raise an issue
