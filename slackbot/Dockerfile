FROM python:slim

RUN pip install slackclient slackeventsapi flask

COPY slackbot.py /app/

CMD /usr/local/bin/python /app/slackbot.py

