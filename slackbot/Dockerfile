FROM python:slim

RUN pip install slack_bolt pika

COPY slackbot.py /app/

CMD /usr/local/bin/python /app/slackbot.py

