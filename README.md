# Overview

This is an image steganography service that takes in a text message, encrypts it with AES-256 encryption and conceals 
the encrypted data inside an image. 
The intent is to demonstrate [LocalStack](https://localstack.cloud/) (a cloud service emulator) to develop and test AWS 
services locally.

## Prerequisites

- [python](https://docs.python.org/3/using/index.html) (version 3.7+)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [docker](https://docs.docker.com/get-docker/)
- [docker-compose](https://docs.docker.com/compose/install/) (version 1.29.2+)

_Optional_: Install [awslocal](https://github.com/localstack/awscli-local) to query the local AWS cloud via CLI: `pip install awscli-local`

## Running locally

There are two ways to run the application locally. 

#### Run completely via docker
* `make` | `make build` - creates a build.zip of the application for the lambda.
* `make run` - deploys localstack container. It creates necessary AWS resources, lambda functions, uploads a test image 
  to the S3 bucket and then submits a message to the SQS which triggers the encryption lambda.
* To retrieve text from the encrypted image, run the decrypt lambda using the following command
  ```
    awslocal lambda invoke --function-name get_secret_text_from_encrypted_image --payload '{"image_path":"s3://images/encrypted_test_image.png", "secret_password_key": "my_pwd"}' --log-type tail /tmp/outfile
  ```
  
#### Run via python with localstack docker
   * Install required dependencies locally by running `pip install -r requirements.txt`
   * Export the following environment variables:
     ```
     AWS_ENDPOINT_URL=http://0.0.0.0:4566
     AWS_ACCESS_KEY_ID=fake_access
     AWS_SECRET_ACCESS_KEY=fake_secret
     ```      
   * `make run` - deploys localstack container. This step only creates the S3 bucket resource and uploads a test image 
     to the S3 bucket.
   * Uncomment the _main_ method at the end of [main.py](src/main.py). It contains the calls to both encrypt and the 
     decrypt methods.
   * Run/debug main.py locally.

#### Validation and Cleanup
* To check for any visual differences between the original image and the image containing hidden text, the latter
  can be downloaded locally using `awslocal s3 cp s3://images/encrypted_test_image.png .`
* `make clean` - removes the artifacts and tears down the network/container.
   
> Note: `make run` uploads the [test_image.png](resources/test_image.png) to s3://images/test_image.png. After `make run`, 
> a wait time of ~30 seconds is usually needed for the localstack container to be initialized completely.

#### Test with custom data:

> Note: Before proceeding, it is assumed that the application is already running and has not been destroyed via `make clean`

- Copy a 'new_test_image.png' to s3: 
  ```
  awslocal s3 cp <new_test_image.png> s3://images/
  ```
- If [running via docker](#run-completely-via-docker), modify the values below and submit this message to the SQS queue:
  ```
    awslocal sqs send-message --queue-url http://localhost:4566/000000000000/image_steganography_queue --message-body '{"image_path":"s3://images/<new_test_image.png>", "secret_text": "<message_to_be_hidden>", "secret_password_key": "<secret_key_to_encrypt_message>"}'
  ```
  The encryption lambda gets triggered and the steganographed image would be uploaded to `s3://images/encrypted_<new_test_image.png>`
- If [running_locally](README.md#run-via-python-with-localstack-docker), just update the arguments to the methods called
  in main.py and run.

#### Interact with other AWS APIs

* SQS
   ```
    awslocal sqs list-queues
    awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/image_steganography_queue
   ```

* S3
   ```
    awslocal s3 ls s3://images/ --recursive
   ```

* Cloudwatch
   ```
    awslocal logs describe-log-groups 
    awslocal logs filter-log-events --log-group-name "/aws/lambda/encrypt_image_with_secret_text"
    awslocal logs describe-log-streams --log-group-name "/aws/lambda/encrypt_image_with_secret_text"
   ```