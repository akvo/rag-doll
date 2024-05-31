FROM python:3.12.3

RUN pip install pika ollama

COPY assistant.py /app/

CMD /usr/local/bin/python /app/assistant.py
