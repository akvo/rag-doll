FROM python:3.12.3

WORKDIR /usr/src/app

COPY . .

RUN apt-get update && apt-get install -y flac ffmpeg

RUN set -e; \
    pip -q install --upgrade pip && \
    pip -q install --no-cache-dir -r requirements.txt && \
    pip check

CMD ["sh", "prod.sh"]
