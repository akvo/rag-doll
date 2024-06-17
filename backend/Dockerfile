FROM python:3.12.3

WORKDIR /usr/src/app

COPY . .

# Copy the rabbitmq_client_package into the container
COPY ../packages/Akvo_rabbitmq_client /app/Akvo_rabbitmq_client

RUN set -e; \
    pip -q install --upgrade pip && \
    pip -q install --no-cache-dir -r requirements.txt && \
    pip check


CMD ["sh", "prod.sh"]
