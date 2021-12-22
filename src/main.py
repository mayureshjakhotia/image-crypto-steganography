import json
import logging
import boto3
from os import environ
from cryptosteganography import CryptoSteganography

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)            # Required by AWS
logging.basicConfig(level=logging.INFO)  # Required for local run

aws_endpoint_url = environ.get('AWS_ENDPOINT_URL')
s3_client = boto3.client('s3', region_name='us-east-1', endpoint_url=aws_endpoint_url)


def _parse_message_from_sqs(event):
    for record in event['Records']:
        return json.loads(record['body'])


def _parse_s3_uri(s3_uri):
    """ Returns bucket, key from the input s3 path """
    tokens = s3_uri.split('/', 3)
    try:
        return tokens[2], tokens[3]
    except IndexError:
        return tokens[2], ''


def _add_secret_text_to_image(s3_input_image_path, secret_text, secret_password_key):
    # Download input s3 image locally
    bucket, key = _parse_s3_uri(s3_input_image_path)
    input_image = key.split('/')[-1]
    s3_client.download_file(bucket, key, f'/tmp/{input_image}')

    # Conceal the image with the secret message (using the secret password key)
    crypto_steganography = CryptoSteganography(secret_password_key)
    output_image = f'concealed_{input_image}'
    logger.info(f'Concealing {input_image} with the secret message')
    crypto_steganography.hide(f'/tmp/{input_image}', f'/tmp/{output_image}', secret_text)

    # Upload the new concealed image to s3
    s3_client.upload_file(f'/tmp/{output_image}', 'images', output_image)
    return f"s3://images/{output_image}"


def _retrieve_secret_text_from_concealed_image(concealed_s3_image_path, secret_password_key):
    # Download concealed s3 image locally
    bucket, key = _parse_s3_uri(concealed_s3_image_path)
    concealed_image = key.split('/')[-1]
    s3_client.download_file(bucket, key, f'/tmp/{concealed_image}')

    # Retrieve the decrypted text using the secret password key
    crypto_steganography = CryptoSteganography(secret_password_key)
    secret_text = crypto_steganography.retrieve(f'/tmp/{concealed_image}')

    return secret_text


def conceal_image_with_secret_text(event, context):
    """
    This handler receives the input s3 image location, the secret text and the secret password key in an SQS message. It
    will create a steganographed image containing the encrypted text and save it to s3 with the prefix 'concealed_'.
    """
    message_body = _parse_message_from_sqs(event)
    input_image_path = message_body['image_path']
    secret_text = message_body['secret_text']
    secret_password_key = message_body['secret_password_key']

    output_image_path = _add_secret_text_to_image(input_image_path, secret_text, secret_password_key)
    logger.info(f'Uploaded the concealed image to {output_image_path}')


def get_secret_text_from_concealed_image(event, context):
    """
    This handler receives the steganographed s3 image and the secret password key. It retrieves the decrypted secret
    text that is hidden in the image.
    """
    concealed_image_path = event['image_path']
    secret_password_key = event['secret_password_key']

    secret_text = _retrieve_secret_text_from_concealed_image(concealed_image_path, secret_password_key)
    logger.info(f'Secret text retrieved from {concealed_image_path}: {secret_text}')

    return {'secret_text': secret_text}


# # Note: This method is just added in order to test directly with Python
# if __name__ == '__main__':
#     # hide text data in an encrypted format inside an image
#     conceal_image_with_secret_text(event={'Records': [{'body': '{"image_path":"s3://images/test_image.png", "secret_text": "This is a secret text", "secret_password_key": "my_pwd"}'}]}, context=None)
#     # get the decrypted text data from the concealed image
#     get_secret_text_from_concealed_image(event={"image_path": "s3://images/concealed_test_image.png", "secret_password_key": "my_pwd"}, context=None)