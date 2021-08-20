import base64
import requests
import datetime

def hello_pubsub(event, context):
    
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    gchat_text = f'{pubsub_message} '
    hangoutschat_data = {'text': gchat_text}
    # Here we get the destination web hook for Google Chat from the cloud function Runtime variables
    # This will be a plain text string of the Google Chat incoming web hook url in human readable form like
    # https://chat.googleapis.com/v1/spaces/XXXXXXXXXXX/messages?key=YYYYYYYYYYYYYYYYYYYYYYYYYYYY&token=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz'
    # https://developers.google.com/chat/quickstart/incoming-bot-python
    
    webhook_url = os.environ.get('gchatHook')
    response = requests.post(webhook_url, json=hangoutschat_data)
    if response.status_code != 200:
        print('Request to Hangouts Chat returned an error %s, the response is:\n%s' % (response.status_code, response.text))
