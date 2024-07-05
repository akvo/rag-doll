# RAG Doll

Rag Doll is a chat-with-your-documents style
[Retrieval Augmented Generation (RAG)](https://www.youtube.com/watch?v=u47GtXwePms),
which is a specialised use of a Large Language Model (LLM) where items from a
knowledge base get added to the prompt for better answers.

There are many RAG implementations out there and I don't proclaim this one to be
better than any of the others. Rag Doll does not support multi-modal chat at
this time. Maybe later, feel free to suggest a pull request. :-)

The implementation is mostly Python, although the heavy lifting is done by
pre-trained machine learning models. You'll want to run this on something with a
decent GPU, or you will find this all to be very slow. Rag Doll is broken up
into several containers, each with a single responsibility (or as close to that
as I could get). Containerising makes it easier to upgrade and improve
individual componetns.


## Assistant

The assistant handles queries to the RAG for us. It awaits messages from the
user chat queue, queries the knowledge base and builds a prompt for the LLM.

| `.env` | default | description |
|---|---|---|
| `ASSISTANT_ROLE` | _CHANGEME_ | The system prompt to the LLM. Describe the assistant's role here. |


## Librarian

The librarian is responsible for getting the knowledge base data into the vector
database. It runs at startup, recreating the data set that is to be used for the
retrieval part of the system.

| `.env` | default | description |
|---|---|---|
| `LIBRARIAN_CORPUS` | _CHANGEME_ | The full path to a gzipped Apache Parquet file with corpus data. |
| `LIBRARIAN_COLLECTION` | knowledge-base | The name of the ChromaDB collection where the corpus will be stored. |


## Ollama LLM Runtime

We use [Ollama](https://ollama.com/) as the model run-time. Ollama makes it easy
to manage multiple models, without having to handle large model files. It also
solves the need for registration on all kinds of sites. Ollama will just pull
the model in and cache it locally.

| `.env` | default | description |
|---|---|---|
| `OLLAMA_HOST` | _CHANGEME_ | The IP address or DNS name of the host that runs Ollama. |
| `OLLAMA_PORT` | 11434 | The port number on the host that runs Ollama. |
| `OLLAMA_CHAT_MODEL` | mistral | The LLM model that is used to handle chat messages. |


## ChromaDB Vector Database

The vector database takes care of embedding and semantic search on the knowledge
base library. Rag doll uses [Chroma DB](https://www.trychroma.com/), being
lightweigth and easy to interface with.

See also [Running Chroma](https://cookbook.chromadb.dev/running/running-chroma/#docker).

| `.env` | default | description |
|---|---|---|
| `CHROMADB_HOST` | chromadb | The hostname of the vector database container. |
| `CHROMADB_HOST` | 8000 | The port that the vector database container listens on. |


## RabbitMQ Message Queueing

In order to separate the Slack and WhatsApp bots, we use message queues. This
allows us to organise and scale workloads, while having each component have only
a single responsibility.

### Queue Message Format

user message:

|field|data type|description|
|---|---|---|
|`id`       | string                                 | Message identification number as the originating platform knows it. |
|`timestamp`| ISO8601 UTC                            | Message timestamp as the originating platform knows it. |
|`platform` | enum: `SLACK`/`WHATSAPP`/`SMS`/`VOICE` | Originating platform. Intended to be able to parse the platform-specific fields. |
|`from`     | platform-specific address              | Enough information for the originating platform to be able to route a reply to this message to where the user expects it. |
|`text`     | UTF-8 string                           | The text as provided by the user. |

from field (where `platform` equals `SLACK` or `WHATSAPP`):

platform Slack format...

platform WhatsApp format... E.164 numbers

| `.env` | default | description |
|---|---|---|
| `RABBITMQ_USER` | rabbit | The user name for RabbitMQ. |
| `RABBITMQ_PASS` | _CHANGEME_ | The default password for accessing queues. Use a generated string. |
| `RABBITMQ_QUEUE_USER_CHATS` | user_chats | The queue for chat messages that the user typed. |
| `RABBITMQ_QUEUE_USER_CHAT_REPLIES` | user_chat_replies | The queue for chat messages that the assisant got from the LLM. |
| `RABBITMQ_EXCHANGE_USER_CHATS` | user_chats_exchange | The topic exchange that routes messages to queues. |
| `RABBITMQ_HOST` | rabbitmq | The host that RabbitMQ runs on. |
| `RABBITMQ_PORT` | 5672 | The AMQP port of RabbitMQ. |
| `RABBITMQ_MANAGEMENT_PORT` | 15672 | The HTTP port for the management web UI of RabbitMQ. |


## Backend and Frontend Overview

### Backend (Fast API)

The backend of this project is built using [FastAPI](https://fastapi.tiangolo.com/), a modern and high-performance web framework for building APIs with Python 3.12.3. The backend communicates with a PostgreSQL database to manage and store application data. The PostgreSQL database is initialized with predefined scripts located in the ./postgres/docker-entrypoint-initdb.d directory, ensuring that the database schema and initial data are set up automatically. Additionally, a PgAdmin4 service is provided to offer a user-friendly interface for managing the PostgreSQL database. PgAdmin4 is configured to run on port 5050 and can be accessed using the default credentials specified in the environment variables.

| `.env` | default | description |
|---|---|---|
| `BACKEND_PORT` | 5000 | The external port used by the Backend |
| `JWT_SECRET` | _CHANGEME_ | JWT-based auth secret key, used in the process of signing a token |
| `MAGIC_LINK_CHAT_TEMPLATE` | _CHANGEME_ | A template for magic link message, e.g. "You can login into APP_NAME by clicking this link: {magic_link}" |


#### Twilio

In the backend, we handle Twilio's send and receive messages through a service called TwilioClient. Currently, we only support WhatsApp text messages.

When started, TwilioClient listens to incoming messages from Twilio using a webhook. TwilioClient will use the frontend port proxy to point to the Twilio callback URL. In Twilio, configure the Sandbox webhook URL to be the external URL for your TwilioClient routes.

The TwilioClient connects to the message queue to interact with the rest of the system, notably the assistant. Incoming messages are forwarded to the `RABBITMQ_QUEUE_USER_CHATS` queue and replies coming from the `RABBITMQ_QUEUE_USER_CHAT_REPLIES` queue are posted back to the user via Twilio.

| `.env` | default | description |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | _CHANGEME_ | The account SID for your Twilio account. |
| `TWILIO_AUTH_TOKEN` | _CHANGEME_ | Your Twilio authorisation token. |
| `TWILIO_WHATSAPP_NUMBER` | _CHANGEME_ | The twilio WhatsApp number from twilio account in international format. |


## Slack Bot

The Slack bot is one of the messaging platforms that can be used to chat with Rag Doll. Most of the Slack interface code was taken from [Getting started with Bolt for Python](https://seratch.github.io/bolt-python/tutorial/getting-started).

The Slack bot listens to incoming messages using a web hook, which is handled nicely by the Bolt framework.

| `.env` | default | description |
|---|---|---|
| `SLACK_BOT_TOKEN` | _CHANGEME_ | The token for your Slack bot. |
| `SLACK_SIGNING_SECRET` | _CHANGEME_ | The signing secret for your Slack bot. |

When installing the Slack Bot, you can use `backend/slackbot-app-manifest.yml` as a template. Before using it, change the following values:

| `slackbot/app-manifest.ymlbackend/slackbot-app-manifest.yml` | default | description |
|---|---|---|
| `description` | _CHANGEME_ | A brief description of the purpose of the bot. |
| `background_color` | _CHANGEME_ | The 6-digit hex colour code for the Slack bot background. |
| `display_name` | _CHANGEME_ | The display name of the Slack bot. This is wat people in your workspace will see. |
| `request_url` | `http://`_CHANGEME_`/slack/events` | The external URL that Slack's servers will use to call the Slack bot component. Replace _CHANGEME_ with the external IP address you reserved for your Google Cloud VM running the components. |

You will also want to upload a nice avatar image to go with your bot.

### Frontend (Next JS)

The frontend of this project is developed using [React with Next.js](https://react.dev/learn/start-a-new-react-project#nextjs-pages-router). In the development environment, the frontend and backend services are configured to facilitate efficient and streamlined development. The frontend, built with React and Next.js, communicates with the backend API using a proxy setup defined in the next.config.js file. This configuration rewrites requests matching the pattern /api/:path* to be forwarded to the backend service at http://backend:5000/api/:path*. This proxy setup simplifies the API call structure during development, allowing developers to interact with the backend as if it were part of the same application.

| `.env` | default | description |
|---|---|---|
| `FRONTEND_PORT` | 3001 | The external port used by the Frontend |

**Frontend**: http://localhost:${FRONTEND_PORT}
**API Docs**: http://localhost:${FRONTEND_PORT}/api/docs#/

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:5000/api/:path*", // Proxy to Backend
      },
    ];
  },
};

export default nextConfig;
```

In the production environment, the interaction between the frontend and backend is handled differently to optimize performance and security. Instead of using the proxy setup defined in the development configuration, the frontend and backend services communicate through an Nginx server. The Nginx configuration, located in the frontend folder, acts as a reverse proxy, efficiently routing requests from the frontend to the backend.

## POSTGRESQL
This project uses PostgreSQL as the backend database for our API.

| `.env` | default | description |
|---|---|---|
| `POSTGRES_PORT` | 5432 | The external port used by the Database |
| `POSTGRES_PASS` | _CHANGEME_ | The default password for accessing Database |
| `PGADMIN_PORT` | 5050 | The external port used by pgadmin page |

## Google Cloud Deployment

This chapter gives a list of items that you should consider as you deploy the
code from this repository. The description assumes you will be deploying to
Google Cloud, so if you deploy on a different cloud provider you may see things
that are different.

I deployed Rag Doll on two virtual machines, mostly because I like to keep
machines as boring and generic as possible. I could not get Ollama to run inside
a Docker container due to the intricacies of GPU support for Docker containers,
so that means I have to install it outside Docker (for now). On top of that, I
would have had to dig into Docker networking. By default you cannot connect to
the host from inside a Docker container. There are ways, of course, but I chose
the quicker route. That's why I ended up with one Docker Compose host and one
Ollama host. You can combine the two if you prefer.

### Disk Space

There are two things that consume a lot of disk space: cached large language
model files and cached Docker files. The stock 10GB disks won't be large enough
for even moderate use of Rag Doll, so you probably want to allocate 100GB
instead. Depending on how you like to organise disks you can get extra attached
storage or just start with larger root disks.

### Reserved IP Addresses

For the most reliable operation, reserve two static IP addresses for Rag Doll;
an internal IP address for Ollama and an external IP address for the Slack API
integration. There are other solutions, of course, but this is simple and you
don't need to edit `.env` each time something has rebooted.

if you choose to run everything on the same machine, you don't need to reserve
an internal IP address for Ollama, but you still need the external IP address
for the Slack API integration.

### Rag Doll using Docker Compose on a Virtual Machine

Getting Rag Doll running is a two-step process: first set up your `.env` file.
The repository contains a template that you can use. It has reasonably sane
defaults for most variables. All that you have to do is add keys and passwords
and you should be good to go.

Copy the template to a file named `.env` and edit that file with your favourite
editor. In the template, search for `CHANGEME` and replace that placeholder with
your own key or generated password. Please do not reuse passwords from other
places, but us a password generator. You won't have to type them, so making them
strong is just as much and as little work as making them weak.

```sh
$ cp env.template .env
$ vi .env
```

All variables are documented in the component documentation sections above. With
`.env` set up, all but one component of Rag Doll can be started with the
following command:

```sh
$ docker compose up
```

### Ollama on a GPU Instance

Even though there is now an official Docker image of Ollama, I still could not
get it running. so for now we host Ollama on its own virtual machine.

Installing Ollama on a clean GPU instance...

Ideally, this would be running as a single Docker compose cluster. That would be
the simplest by far. Unfortunately, I've not had the time to dig into running
Ollama on GPUs inside a Docker container on the Google Cloud. This is not
trivial, so until I sorted that out I chose to split Ollama out onto its own
machine. I thought about running it on baremetal alongside the Docker compose
containers, but then I'd have to wade into Docker's networking weeds. A separate
machine is just as easy.

So while most of the system can be constructed using a simple `docker compose up`,
for Ollama there is a separate installation instruction.

On the GPU instance, follow the instructions here: [Running Llama 3 models locally on CPU machines](https://yang3kc.substack.com/p/running-llama-3-models-locally-on). Yes, that reads "CPU" and not "GPU", not sure what that is about.

```sh
$ find . -name ollama.service
$ sudo vi ./system/ollama.service
$ systemctl daemon-reload
$ sudo systemctl daemon-reload
$ sudo systemctl restart ollama
```

https://github.com/ollama/ollama/blob/main/docs/faq.md

Also: `nvtop` is awesome!

### Allocate GPU Instance on Google Cloud

Allocating a GPU instance on the Google Cloud is hard, because everyone us vying
for the same resources. Most of the time your start request will be denied for
lack of resources. So here is what I do: open the Google Cloud Shell and
programmatically try to start the instance. If it fails, wait for a bit and
try again. It can take well over an hour for you to be able to start it, so
leave this running and do something else in the mean time.

```sh
$ until gcloud compute instances start rag-doll-t4 --zone europe-central2-b; do date; echo "waiting..."; sleep 2; done
```

Replace `rag-doll-t4` with the name and `europe-central2-b` with the zone name
for your virtual machine.


### Docker Logger Crash Prevention

It is well know that Docker eats disk space relentlessly. One particular problem
is that the default logger format for Docker, `json-file`, does not support log
rotation. Instead, switch Docker over to using the `local` logging driver. That
does support log rotation. See
[Configure logging drivers](https://docs.docker.com/config/containers/logging/configure/)
for instructions.

```sh
$ docker info --format '{{.LoggingDriver}}'
json-file
$ sudo vi /etc/docker/daemon.json
{
    "log-driver": "local"
}
$ sudo systemctl restart docker
$ docker info --format '{{.LoggingDriver}}'
local
```
