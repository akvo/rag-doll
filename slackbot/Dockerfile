FROM python:slim

RUN pip install slack_bolt

COPY slackbot.py /app/

CMD /usr/local/bin/python /app/slackbot.py

