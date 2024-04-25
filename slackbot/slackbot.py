import os
import slack
from flask import Flask
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)

slack_client = slack.WebClient(token=os.getenv('SLACKBOT_TOKEN'))
slack_events = SlackEventAdapter(os.getenv('SLACKBOT_SIGNING_SECRET') ,'/slack/events', app)

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

