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
individual components.


## Assistant

The assistant handles queries to the RAG for us. It awaits messages from the
user chat queue, queries the knowledge base and builds a prompt for the LLM.

We use [OpenAI](https://platform.openai.com/) as the model run-time. OpenAI
provides robust capabilities for managing multiple models and handling large
model files. It simplifies the integration process by managing registrations and
pulling models as needed.

| `.env` | default | description |
|---|---|---|
| `ASSISTANT_LANGUAGES` | `en`, _CHANGEME_, _CHANGEME_ | A comma-separated list of ISO 639-1 language codes. Be sure to add a section to the system prompt that describes these languages.  |
| `SYSTEM_PROMPT_{language}` | _CHANGEME_ | The system prompt to the LLM in language `{language}`. Describe the assistant's role here. |
| `RAG_PROMPT_{language}`     | "{prompt}. In your answer, use the following information if it is related: {context}" | The RAG enabled prompt for the LLM. The `{prompt}` placeholder is for the client question and `{context}` is where the RAG context is added. |
| `RAGLESS_PROMPT_{language}` | "{prompt}" | The prompt in case there is no usable RAG context. The `{prompt}` placeholder is where the client's question is added. |
| `OPENAI_API_KEY` | _CHANGEME_ | The API key for authenticating with OpenAI services. |
| `OPENAI_CHAT_MODEL` | `gpt-4o` | The LLM model that is used to handle chat messages. Read more about [OpenAI models](https://platform.openai.com/docs/models) |
| `CHROMADB_DISTANCE_CUTOFF` | `1.5` | The minimum vector distance needed for a chunk for the chunk to be included in the prompt as RAG context. Chunks with a higher distance are discarded from the RAG query results. |

For the final configuration, be sure to add one each of system prompt, RAG
prompt and RAG-less prompt for all langauges in `ASSISTANT_LANGUAGES`. This
gives the system a specific set of prompts for each language. All language codes
are ISO 639-1 codes.

Note: The __OPENAI_API_KEY__ does not need to be explicitly called in
[assistant.py](https://github.com/akvo/rag-doll/blob/master/assistant/assistant.py)
because the openai library automatically reads it from the environment variables
when `openai.OpenAI()` is instantiated.


## EPPO Librarian

The EPPO librarian is responsible for getting the EPPO Global Database data
sheet data into the vector database. It runs at startup, recreating the data set
that is to be used for the retrieval part of the system.

The [EPPO Global Database](https://gd.eppo.int/) is a collection of technical
resources that researchers can use in their work. As quoted from their website:
*EPPO Global Database is maintained by the Secretariat of the European and
Mediterranean Plant Protection Organization (EPPO). The aim of the database is
to provide all pest-specific information that has been produced or collected by
EPPO. The database contents are constantly being updated by the EPPO
Secretariat.*

| `.env` | default | description |
|---|---|---|
| `CHROMADB_COLLECTION_TEMPLATE` | EPPO-datasheets-{} | The template for the names of the ChromaDB collections where each translation of the EPPO datasheets will be stored. This should have one `{}` placeholder. |
| `EPPO_COUNTRY_ORGANISM_URL` | https://gd.eppo.int/country/{country}/organisms.csv | The URL to the per-country organism list on the EPPO database. Use `{country}` as placeholder for the country to query for. |
| `EPPO_DATASHEET_URL` | https://gd.eppo.int/taxon/{eppo_code}/datasheet | The URL to the organism datasheet in the EPPO database. Use `{eppo_code}` as placeholder for the EPPO code. |
| `EPPO_COUNTRIES` | _CHANGEME_ | A comma-separated list of ISO 3166-1 alpha-2 country codes of countries that you are interested in. |
| `CHUNK_SIZE` | 5 | For small data sets, a few sentences will have to do. |
| `OVERLAP_SIZE` | 1 | The EPPO librarian uses rooftiling. This is the overlap. |

EPPO is not completely clear on what license they expect. They do not restrict
accessing the datasheets. They do ask for citation, which we provide.


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

In order to communicate between the services we use message queues. This allows
us to organise and scale workloads, while having each component have only a
single responsibility.

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


## Backend (Fast API)

The backend of this project is built using [FastAPI](https://fastapi.tiangolo.com/), a modern and high-performance web framework for building APIs with Python 3.12.3. The backend communicates with a PostgreSQL database to manage and store application data. The PostgreSQL database is initialized with predefined scripts located in the ./postgres/docker-entrypoint-initdb.d directory, ensuring that the database schema and initial data are set up automatically. Additionally, a PgAdmin4 service is provided to offer a user-friendly interface for managing the PostgreSQL database. PgAdmin4 is configured to run on port 5050 and can be accessed using the default credentials specified in the environment variables.

| `.env` | default | description |
|---|---|---|
| `BACKEND_PORT` | 5000 | The external port used by the Backend |
| `JWT_SECRET` | _CHANGEME_ | JWT-based auth secret key, used in the process of signing a token |
| `WEBDOMAIN` | "http://localhost" | The base URL of the web application |
| `MAGIC_LINK_CHAT_TEMPLATE` | _CHANGEME_ | A template for magic link message, e.g. "You can login into APP_NAME by clicking this link: {magic_link}" |

### Chat Session Seeder

Before using the application, you can seed the database with user, client, and chat session data using the `chat_session` seeder. Follow the instructions below to set up and run the seeder.

#### Google Sheet Template

Prepare a Google Sheet with the following columns (or you can use this [template](https://docs.google.com/spreadsheets/d/1ev7-wZbFZU_IpN4KL1XQlaVpCbH3JyOXsNB0r69Dbbw/edit?gid=0#gid=0)):
- `client_phone_number`: Phone number of the client (including the + sign).
- `client_name`: Name of the client (can be empty).
- `linked_to_user_phone_number`: Phone number of the user linked to the client (including the + sign).
- `user_name`: Name of the user (can be empty).

Ensure that the Google Sheet is publicly accessible.

#### Running the Seeder

1. Save your data in the prepared Google Sheet template.
2. From the backend directory, run the following command:

    ```bash
    python -m seeder.chat_session
    ```

3. The script will prompt you for the Google Sheet ID, which can be found in the URL of the Google Sheet. Enter the ID and press Enter.

4. The seeder will process the data and populate your database with the user, client, and chat session information.


### Twilio Channel

In the backend, we handle Twilio's send and receive messages through a service
called `TwilioClient`. Currently, we only support WhatsApp text messages.

When started, `TwilioClient` listens to incoming messages from Twilio using a
webhook. `TwilioClient` will use the frontend port proxy to point to the Twilio
callback URL. In Twilio, configure the sandbox webhook URL to be the external
URL for your `TwilioClient` routes.

The `TwilioClient` connects to the message queue to interact with the rest of
the system, notably the assistant. Incoming messages are forwarded to the
`RABBITMQ_QUEUE_USER_CHATS` queue and replies coming from the
`RABBITMQ_QUEUE_USER_CHAT_REPLIES` queue are posted back to the user via Twilio.

| `.env` | default | description |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | _CHANGEME_ | The account SID for your Twilio account. |
| `TWILIO_AUTH_TOKEN` | _CHANGEME_ | Your Twilio authorisation token. |
| `TWILIO_WHATSAPP_NUMBER` | _CHANGEME_ | The twilio WhatsApp number from twilio account in international format. |

### Slack Channel

Slack is one of the messaging platforms that can be used to chat with Rag Doll.
Most of the Slack interface code was taken from
[Getting started with Bolt for Python](https://seratch.github.io/bolt-python/tutorial/getting-started).

The Slack client in the backend listens to incoming messages using a web hook,
which is handled nicely by the Bolt framework.

| `.env` | default | description |
|---|---|---|
| `SLACK_BOT_TOKEN` | _CHANGEME_ | The token for your Slack bot. |
| `SLACK_SIGNING_SECRET` | _CHANGEME_ | The signing secret for your Slack bot. |

When installing the the backend as Slack App, you can use
`backend/slackbot-app-manifest.yml` as a template. Before using it, change the
following values:

| `backend/slackbot-app-manifest.yml` | default | description |
|---|---|---|
| `description` | _CHANGEME_ | A brief description of the purpose of the bot. |
| `background_color` | _CHANGEME_ | The 6-digit hex colour code for the Slack bot background. |
| `display_name` | _CHANGEME_ | The display name of the Slack bot. This is wat people in your workspace will see. |
| `request_url` | `http://`_CHANGEME_`/slack/events` | The external URL that Slack's servers will use to call the Slack bot component. Replace _CHANGEME_ with the external IP address you reserved for your Google Cloud VM running the components. |

You will also want to upload a nice avatar image to go with your bot.


## Frontend (Next JS)

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


## PostgreSQL

This project uses PostgreSQL as the backend database.

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

### Disk Space

Cached Docker files and images consume a lot of disk space. The stock 10GB disks
won't be large enough for Rag Doll, so you probably want to allocate 100GB
instead. Depending on how you like to organise disks you can get extra attached
storage or just start with larger root disks.

### Reserved IP Address

Reserve a static IP address for the webhook calls from Twilio and Slack.

### Rag Doll using Docker Compose on a Virtual Machine

Getting Rag Doll running is a two-step process: first set up your `.env` file.
The repository contains a template that you can use. It has reasonably sane
defaults for most variables. All that you have to do is add keys and passwords
and you should be good to go.

Copy `env.template` to `.env` and edit that file with your favourite editor. In
the template, search for `CHANGEME` and replace that placeholder with your own
key or generated password. Please do not reuse passwords from other places, but
us a password generator. You won't have to type them, so making them strong is
just as much and as little work as making them weak.

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
