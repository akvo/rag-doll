FROM python:slim

RUN apt update && apt install -y build-essential
RUN pip install chromadb pika

COPY archivist.py /app/

CMD /usr/local/bin/python /app/archivist.py

