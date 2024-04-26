import os
import re
import logging
from typing import Callable

from slack_sdk import WebClient
from slack_bolt import App, Say, BoltContext

from ollama import Client
ROLE_USER='user'
ROLE_SYSTEM='system'
ROLE_ASSISTANT='assistant'
MSG_MESSAGE='message'
MSG_ROLE='role'
MSG_CONTENT='content'
MSG_RESPONSE='response'
MSG_STATUS='status'
MSG_SUCCESS='success'

logging.basicConfig(level=logging.DEBUG)

# --- Assistant section

class LLM:
    def __init__(self, chat_model, image_model):
        llm_client = Client(host=f"http://{os.getenv("OLLAMA_HOST")}:{os.getenv("OLLAMA_PORT")}")
        self.chat_model = chat_model
        pull_response = llm_client.pull(self.chat_model)
        if pull_response[MSG_STATUS] != MSG_SUCCESS:
            raise Exception(f"failed to pull {self.chat_model}: {pull_response}")

        self.image_model = image_model
        pull_response = llm_client.pull(self.image_model)
        if pull_response[MSG_STATUS] != MSG_SUCCESS:
            raise Exception(f"failed to pull {self.image_model}: {pull_response}")

        self.messages = []
        self.append_message(ROLE_SYSTEM, "You are a Kenyan Extension Officer, specialised in agriculture. You cannot answer questions that are not about agriculture.")

    def chat(self, content):
        self.append_message(ROLE_USER, content)
        response = llm_client.chat(model=self.chat_model, messages=self.messages)
        message = response[MSG_MESSAGE]
        self.append_message(message[MSG_ROLE], message[MSG_CONTENT])
        return message[MSG_CONTENT]

    def check_image(self, image):
        self.append_message(ROLE_USER, f"{IMAGE_PROMPT}: {image}")
        response = llm_client.generate(model=self.image_model, prompt=IMAGE_PROMPT, images=[image])
        message = response[MSG_RESPONSE]
        self.append_message(ROLE_ASSISTANT, message)
        return f"I looked at {image}. {message}"

    def append_message(self, role, content):
        self.messages.append({MSG_ROLE: role, MSG_CONTENT: content})
        # print(f"------- {self.messages}")

llm = LLM('mistral', 'llava')

# --- Slack section

app = App(token=os.environ.get("SLACK_BOT_TOKEN"),
          signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))

@app.middleware
def log_request(logger: logging.Logger, body: dict, next: Callable):
    logger.debug(body)
    return next()


# middleware function
def extract_subtype(body: dict, context: BoltContext, next: Callable):
    context["subtype"] = body.get("event", {}).get("subtype", None)
    next()


# https://api.slack.com/events/message
# Newly posted messages only
# or @app.event("message")
@app.event({"type": "message", "subtype": None})
def reply_in_thread(body: dict, say: Say):
    event = body["event"]
    logger.info(event)

    text = body["event"]["text"]
    llm_response = llm.chat(text)

    thread_ts = event.get("thread_ts", None) or event["ts"]
    say(text=llm_response, thread_ts=thread_ts)


@app.event(
    event={"type": "message", "subtype": "message_deleted"},
    matchers=[
        # Skip the deletion of messages by this listener
        lambda body: "You've deleted a message: "
        not in body["event"]["previous_message"]["text"]
    ],
)
def detect_deletion(say: Say, body: dict):
    text = body["event"]["previous_message"]["text"]
    say(f"You've deleted a message: {text}")


# https://api.slack.com/events/message/file_share
# https://api.slack.com/events/message/bot_message
@app.event(
    event={"type": "message", "subtype": re.compile("(me_message)|(file_share)")},
    middleware=[extract_subtype],
)
def add_reaction(body: dict, client: WebClient, context: BoltContext, logger: logging.Logger):
    subtype = context["subtype"]  # by extract_subtype
    logger.info(f"subtype: {subtype}")
    message_ts = body["event"]["ts"]
    api_response = client.reactions_add(
        channel=context.channel_id,
        timestamp=message_ts,
        name="eyes",
    )
    logger.info(f"api_response: {api_response}")


# This listener handles all uncaught message events
# (The position in source code matters)
@app.event({"type": "message"}, middleware=[extract_subtype])
def just_ack(logger, context):
    subtype = context["subtype"]  # by extract_subtype
    logger.info(f"{subtype} is ignored")


# XXX
# @slack_events.on('message')
# def on_message(payload):
#     event = payload.get('event')
#
#     channel = event.get('channel')
#     user = event.get('user')
#     text = event.get('text')
#
#     print(f"{user}{channel}: {text}")

app.start(port=int(os.getenv('SLACK_BOT_PORT')))

