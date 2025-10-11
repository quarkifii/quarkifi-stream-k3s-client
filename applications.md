## Manage Applications

Once the Edge Device is configured you can create applications over the K3S container system remotely managed from Quarkifi Stream. 
To manage Applications from the edge device click on Device Actions -> View Applications

![Edge Applications](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-171003.png)

One can manage two types of applications using Quarkifi Edge Orchestrator for K3S.

1. Docker Image From Registry
2. Upload Custom Docker Image

### Create Application Using Docker Image From Registry

1. Click Add to create Application

![Application Add Button](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162518.png)

2. Fill up following details in the application form
   - Select Image Type as 'Use Docker Image' to use standard docker image from registry
   - Provide the docker Image Name 
   - Provide a user specific app version
   - Provide a user friendly name to identify the application
   - One can create multiple instance by setting the no of replicas
   - One can setup optional volume and other container options in Advance Options

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-171624.png)

3. Click on Deploy to deploy the new application.
   - It may take some time to make the application ready.
   - Please wait till the processing of the deployment is over

![Processing Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174131.png)

4. Once deployed you should be able to see the running state of the application

![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174425.png)

5. Once deployed click on App Actions -> Show Logs
   - This will show the application logs.
   - The application is now ready and in running state if the logs are fine and as expected

![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174631.png)

### Create Application Upload Custom Built Docker Image

#### Build Docker Image for Target Architecture

Example: If you are generating docker image for raspberrypi board you can use below command to generate the .gz file to be used for upload.

```bash
# cmd: sudo docker buildx build --platform linux/arm64 -t log-newimage:v2 --output type=docker,dest=image-processor-pi.tar .
# cmd: gzip image-processor-pi.tar
```
This will generate the gz image (e.g image-processor-pi.tar.gz) which can be used to upload to the edge device for deployment as an application.

## Create Application Using Image Upload

1. Click Add to create Application

![Application Add Button](https://qstream.quarkifi.com/wp-content/uploads/2025/09/Screenshot-2025-09-08-162518.png)

2. Fill up following details in the application form
   - Select Image Type as 'Upload Image' to upload image generated locally
   - Click on Select Docker Image

![Add Application Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-181823.png)

3. Once Selected the form will show the selected image

![Selected Image Form](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-182312.png)

4. Upload the selected image

![Upload Image](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-184008.png)

5. Once Uploaded it would open a Application Form
   Fill up following details in the application form:
   - Select Image Type as 'Upload Image' to use uploaded Image
   - Provide a user specific app version
   - Provide a user friendly name to identify the application
   - One can create multiple instance by setting the no of replicas
   - One can setup optional volume and other container options in Advance Options

![Application Form After Upload](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-184244.png)

6. Click on Deploy to deploy the new application.
   - It may take some time to make the application ready.
   - Please wait till the processing of the deployment is over

![Processing Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174131.png)

7. Once deployed you should be able to see the running state of the application

![Running Application State](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174425.png)

8. Once deployed click on App Actions -> Show Logs
   - This will show the application logs.
   - The application is now ready and in running state if the logs are fine and as expected

![Application Logs](https://qstream.quarkifi.com/wp-content/uploads/2025/10/Screenshot-2025-10-11-174631.png)

## Application Management Actions

Once applications are deployed, you can perform various management actions:

- **Start/Stop Applications**: Control application state
- **Scale Replicas**: Adjust the number of running instances
- **Analyze Logs**: Analyze logs of the container application
- **Update Configuration**: Modify environment variables and settings
- **View Metrics**: Monitor resource usage and performance
- **Delete Applications**: Remove deployed applications

## Troubleshooting

### Common Issues and Solutions

1. **Application Not Starting**
   - Check if the Docker image architecture matches the edge device
   - Verify that all required environment variables are set
   - Review application logs for error messages

2. **Image Upload Failures**
   - Ensure the uploaded file is a valid Docker image archive
   - Check file size limits and network connectivity
   - Verify the image is built for the correct platform (ARM64 for Raspberry Pi)

3. **Deployment Timeouts**
   - Check edge device connectivity to Quarkifi Stream
   - Verify K3S is running properly on the edge device
   - Monitor resource constraints (CPU, memory, storage)

## Best Practices

1. **Image Optimization**
   - Use multi-stage builds to reduce image size
   - Choose appropriate base images for your target architecture
   - Regularly update and patch your container images

2. **Application Configuration**
   - Use environment variables for configuration
   - Implement proper health checks
   - Set appropriate resource limits and requests

3. **Monitoring and Logging**
   - Implement structured logging
   - Set up proper monitoring and alerting
   - Regularly review application logs and metrics

## More Information

More information about Quarkifi Stream Platform can be found [here](https://qstream.quarkifi.com).

For any issue please reach out to support@quarkifi.com or raise an issue.

## License

This library is [licensed](LICENSE) under the [MIT Licence](https://en.wikipedia.org/wiki/MIT_License).

For any issue please reach out to support@quarkifi.com or raise an issue.
