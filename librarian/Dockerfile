FROM python:3.12.3

RUN apt update && apt install -y build-essential
RUN pip install pandas pyarrow chromadb

COPY librarian.py /app/

CMD /usr/local/bin/python /app/librarian.py
