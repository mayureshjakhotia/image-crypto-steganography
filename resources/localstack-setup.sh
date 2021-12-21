#!/usr/bin/env bash

echo "Creating required S3 bucket"
awslocal s3api create-bucket --bucket images

echo "Copying input test image to s3"
awslocal s3 cp /resources/test_image.png s3://images/test_image.png

ZIP_FILE=/resources/lambda-layer.zip
if [ -f "$ZIP_FILE" ]; then
echo "$ZIP_FILE exists."

echo "Creating the lambda function to encrypt text within image"
awslocal lambda create-function --function-name encrypt_image_with_secret_text \
    --zip-file fileb:///resources/lambda-layer.zip \
    --handler main.encrypt_image_with_secret_text \
    --environment Variables="{$(cat < /resources/.env | xargs | sed 's/ /,/g')}" \
    --runtime python3.7 \
    --role whatever


echo "Creating the lambda function to retrieve text from image"
awslocal lambda create-function --function-name get_secret_text_from_encrypted_image \
    --zip-file fileb:///resources/lambda-layer.zip \
    --handler main.get_secret_text_from_encrypted_image \
    --environment Variables="{$(cat < /resources/.env | xargs | sed 's/ /,/g')}" \
    --runtime python3.7 \
    --role whatever


echo "Creating required SQS queue"
awslocal sqs create-queue --queue-name image_steganography_queue

echo "Binding Lambda to SQS queue"
awslocal lambda create-event-source-mapping --function-name encrypt_image_with_secret_text --batch-size 1 --event-source-arn arn:aws:sqs:us-east-1:000000000000:image_steganography_queue

echo "Trigger encryption lambda by sending a message to the SQS"
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/image_steganography_queue --message-body '{"image_path":"s3://images/test_image.png", "secret_text": "This is a secret text", "secret_password_key": "my_pwd"}'

else
    echo "$ZIP_FILE does not exist ie. triggered directly via Python."
fi