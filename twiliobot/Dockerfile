FROM python:slim

RUN pip install twilio pika flask

COPY twiliobot.py /app/
COPY test.py /app/

CMD /usr/local/bin/python /app/twiliobot.py

