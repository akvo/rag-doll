FROM python:3.12.3

WORKDIR /usr/src/app

COPY . .

COPY ./packages/Akvo_rabbitmq_client /app/Akvo_rabbitmq_client

RUN set -e; \
    pip -q install --upgrade pip && \
    pip -q install --no-cache-dir -r requirements.txt && \
    pip check

CMD ["sh", "prod.sh"]