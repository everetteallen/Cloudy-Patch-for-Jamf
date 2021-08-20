import base64
import requests
import json
from flask import jsonify

def hello_pubsub(event, context):
    
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    slack_text = {"text" : f"{pubsub_message}"}
    
    # Here we get the destination web hook for Slack from the cloud function Runtime variables
    # This will be a plain text string of the slack web hook url in human readable form like
    # https://hooks.slack.com/services/XXXXXXXXX/YYYYYYYY/zzzzzzzzzzzzzzzzz
    # See https://slack.com/help/articles/115005265063-Incoming-webhooks-for-Slack
    
    webhook_url = os.environ.get('slackHook')
    
    response = requests.post(webhook_url, json=slack_text, headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        print('Request to Slack returned an error %s, the response is:\n%s' % (response.status_code, response.text))
