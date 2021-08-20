import sys
from flask import escape 
from flask import json
import datetime
from google.cloud import pubsub_v1

# [START functions_CPJUpdater]
def CPJUpdater(request):
   
    request_json = request.get_json(silent=True)
    request_args = request.args
    if request_json and 'event' in request_json:
        event = request_json['event']
        name = event['name']
        version = event['latestVersion']
        when = datetime.datetime.fromtimestamp(int(event['lastUpdate'])/1000)
    elif request_args and 'name' in request_args:
        name = request_args['name']
    else:
        name = 'World'
    
    # Get the event type in case we have to handle others in the future
    if request_json and 'webhook' in request_json:
        webh = request_json['webhook']
        webhook_event = webh['webhookEvent']
    else:
        webhook_event = 'Unknown'

    # Notify the Slack and GChat CPJnotifiers we have a path title update
    message = ( f'*{webhook_event} -- The Patch Title for {name} was upated for version {version} at {when} ').encode()
    publisher = pubsub_v1.PublisherClient()
    
    # Here we get from the Cloud function environment the Run Time environment variables we have set 
    # for the PubSub topics making this portable. These will be a string of the format 
    # projects/<yourprojectname>/topics/CPJNotifer
    # assuming the notifier function is in the same GCS project 
    
    topic_name = os.environ.get('topicCPJName') 
    topic_download = os.environ.get('topicCPJDownload')
    
    # publish to the notifiers
    publisher.publish(topic_name, message)

    # Notify the CPJDownloader to check for packages
    data_download = ( f'{name}, {version}')
    message_download = data_download.encode()
    publisher_download =  pubsub_v1.PublisherClient()
    
    publisher_download.publish(topic_download, message_download)

    return '200'
# [END functions_CPJUpdater]