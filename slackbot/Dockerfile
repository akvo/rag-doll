FROM python:slim

RUN pip install slack_bolt pika ollama

COPY slackbot.py /app/

CMD /usr/local/bin/python /app/slackbot.py

