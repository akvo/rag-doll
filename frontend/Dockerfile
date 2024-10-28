FROM akvo/akvo-node-18-alpine:20230831.105309.b9593b7

WORKDIR /app

COPY . .

# Define build-time arguments for environment variables
ARG FRONTEND_PORT
ARG BACKEND_PORT
ARG NEXT_PUBLIC_VAPID_PUBLIC_KEY
ARG NEXT_PUBLIC_VAPID_PRIVATE_KEY

# Write each variable into the .env file inside the container
RUN echo "FRONTEND_PORT=${FRONTEND_PORT}" > .env && \
    echo "BACKEND_PORT=${BACKEND_PORT}" >> .env && \
    echo "NEXT_PUBLIC_VAPID_PUBLIC_KEY=${NEXT_PUBLIC_VAPID_PUBLIC_KEY}" >> .env && \
    echo "NEXT_PUBLIC_VAPID_PRIVATE_KEY=${NEXT_PUBLIC_VAPID_PRIVATE_KEY}" >> .env

EXPOSE 3000

CMD [ "yarn", "start" ]