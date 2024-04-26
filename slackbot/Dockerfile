FROM python:slim

RUN pip install slack_bolt ollama

COPY slackbot.py /app/

CMD /usr/local/bin/python /app/slackbot.py

