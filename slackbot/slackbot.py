import os
import hmac
import slack
from flask import Flask, request
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)

SLACKBOT_SIGNING_SECRET = os.getenv('SLACKBOT_SIGNING_SECRET')

# https://stackoverflow.com/questions/64341222/how-to-validate-slack-api-request
@app.route('/slack-validation', methods=['GET', 'POST']) 
def slack_validation():
    headers = request.headers
    timestamp = request.headers['X-Slack-Request-Timestamp'] 

    slack_payload = request.form
    dict_slack = slack_payload.to_dict()

### This is the key that solved the issue for me, where urllib.parse.quote(val, safe='')] ###
    payload= "&".join(['='.join([key, urllib.parse.quote(val, safe='')]) for key, val in dict_slack.items()])  

    ### compose the message:
    sig_basestring = 'v0:' + timestamp + ':' + payload

    sig_basestring = sig_basestring.encode('utf-8')

    ### secret
    signing_secret = SLACKBOT_SIGNING_SECRET.encode('utf-8') # I had an env variable declared with slack_signing_secret
    
    my_signature = 'v0=' + hmac.new(signing_secret, sig_basestring, hashlib.sha256).hexdigest()
    print('my signature: ')
    print(my_signature)
    
    return '', 200


slack_client = slack.WebClient(token=os.getenv('SLACKBOT_TOKEN'))
slack_events = SlackEventAdapter(SLACKBOT_SIGNING_SECRET ,'/slack/events', app)

@slack_events.on('message')
def on_message(payload):
    event = payload.get('event')
    channel = event.get('channel')
    user = event.get('user')
    text = event.get('text')

    print(f"{user}{channel}: {text}")

response = slack_client.chat_postMessage(channel='#rag-doll', text='hello world')
if not response['ok']:
    print(f"unable to send message: {response}")

print(f"running on http://{os.getenv('SLACKBOT_HOST')}:{int(os.getenv('SLACKBOT_PORT'))}...")
app.run(host=os.getenv('SLACKBOT_HOST'), port=int(os.getenv('SLACKBOT_PORT')))

