FROM python:slim

RUN apt update && apt install -y build-essential
RUN pip install chromadb paho-mqtt

COPY archivist.py /app/

CMD /usr/local/bin/python /app/archivist.py

