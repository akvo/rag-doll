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


## Slack Bot

The Slack bot is the first interface that can be used to chat with the rag doll.
Slack is a little more convenient to use than WhatsApp and it does mostly the
same. Good enough for a demo.

Most of the Slack interface code was taken from
[Getting started with Bolt for Python](https://seratch.github.io/bolt-python/tutorial/getting-started).

| `.env` | default | description |
|---|---|---|
| `SLACK_BOT_PORT` | 3000 | The external port used by the Bolt framework. This is where Slack's servers connect to, so open it on the firewall. |
| `SLACK_BOT_TOKEN | _CHANGEME_ | The token for your Slack bot. |
| `SLACK_SIGNING_SECRET` | _CHANGEME_ | The signing secret for your Slack bot. |


## Assistant
The assistant handles queries to the RAG for us. It awaits messages from the
user chat queue, queries the knowledge base and builds a prompt for the LLM.

| `.env` | default | description |
|---|---|---|
| `ASSISTANT_ROLE | _CHANGEME_ | The system prompt to the LLM. |


## Librarian
The librarian is responsible for getting the knowledge base data into the vector
database. It runs at startup, recreating the data set that is to be used for the
retrieval part of the system.



## Ollama LLM Runtime
We use [Ollama](https://ollama.com/) as the model run-time. Ollama makes it easy
to manage multiple models, without having to handle large model files. It also
solves the need for registration on all kinds of sites. Ollama will just pull
the model in and cache it locally.

In order for Ollama to be able to use the system's GPU (only works on Linux),
install
[NVidea's Container Toolkit](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image)
first. This must run on the Docker host and not inside a container, hence the
need to do a separate installation.

If you get the error `Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]`, you may have forgotten to run the [configuration step of the NVIDIA Container Toolkit installation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuration).

Unfortunately, this ends an with error that I have so far failed to resolve:
`Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error running hook #0: error running hook: exit status 1, stdout: , stderr: Auto-detected mode as 'legacy'
nvidia-container-cli: initialization error: load library failed: libnvidia-ml.so.1: cannot open shared object file: no such file or directory: unknown`

Maybe try: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html ?

See also:
- [Turn on GPU access with Docker Compose](https://docs.docker.com/compose/gpu-support/)
- [Installing the NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)


## ChromaDB Vector Database
The vector database takes care of embedding and semantic search on the knowledge
base library.

Rag doll uses [Chroma DB](https://www.trychroma.com/), being lightweigth and
easy to interface with.

See also [Running Chroma](https://cookbook.chromadb.dev/running/running-chroma/#docker).


## RabbitMQ Message Queueing
In order to separate the Slack and WhatsApp bots, we use message queues. This
allows us to organise and scale workloads, while having each component have only
a single responsibility.

### Queue Message Format

user message:
|---|---|---|
|field|data type|description|
|`id`       | string                                 | Message identification number as the originating platform knows it. |
|`timestamp`| ISO8601 UTC                            | Message timestamp as the originating platform knows it. |
|`platform` | enum: `SLACK`/`WHATSAPP`/`SMS`/`VOICE` | Originating platform. Intended to be able to parse the platform-specific fields. |
|`from`     | platform-specific address              | Enough information for the originating platform to be able to route a reply to this message to where the user expects it. |
|`text`     | UTF-8 string                           | The text as provided by the user. |
|---|---|---|

from field (where `platform` equals `SLACK`):


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

### Firewall Rules

Slack needs to be able to connect to the `slackbot` container, on port
`SLACK_BOT_PORT`. Set up a firewall rule with the name `allow-slackbot` that
allows traffic to that port to connect and set the associated tag on the network
configuration of your vistual machine that hosts the `slackbot` Docker container.

### Rag Doll on a Virtual Machine

All but one component of Rag Doll can be started with the following command:

```sh
$ docker compose up
```


### Ollama on a GPU Instance

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

341  find . -name ollama.service
  342  sudo vi ./system/ollama.service
  343  systemctl daemon-reload
  344  sudo systemctl daemon-reload
  345  sudo systemctl restart ollama
  346  history

https://github.com/ollama/ollama/blob/main/docs/faq.md

Also: `nvtop` is awesome!

### Allocate GPU Instance on Google Cloud
Allocating a GPU instance on the Google Cloud is hard, because everyone us vying
for the same resources. Most of the time your start request will be denied for
lack of resources. So here is what I do: open the Google Cloud Shell and
programmatically try to start the instance. If it fails, wait for a bit and
try again. It can take well over an hour for you to be able to start it, so
leave this running and do something else in the mean time.

`until gcloud compute instances start rag-doll-t4 --zone europe-central2-b; do date; echo "waiting..."; sleep 2; done`

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


### Attach Google Cloud Storage as Disk
Ollama will download models and these can be huge too, so you need ample disk
space for the cached models. Here is a reminder how to attach storage as disk to
your virtual machine instance.

```sh
$ ls -l /dev/disk/by-id/google-*
$ sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb
$ sudo mkdir /tank
$ sudo blkid /dev/sdb
/dev/sdb: UUID="85acf249-c912-4f80-83da-bc6931119519" BLOCK_SIZE="4096"
TYPE="ext4" PARTUUID="593b3b75-108f-bd41-823d-b7e87d2a04d1"
UUID=UUID_VALUE /mnt/disks/MOUNT_DIR ext4 discard,defaults,MOUNT_OPTION 0 2
$ sudo vi /etc/fstab
```

## Slack Bot
The Slack bot is the first interface that can be used to chat with the rag doll.
Slack is a little more convenient to use than WhatsApp and it does mostly the
same. Good enough for a demo.

Most of the Slack interface code was taken from
[Getting started with Bolt for Python](https://seratch.github.io/bolt-python/tutorial/getting-started).


## Assistant
The assistant handles queries to the RAG for us. It awaits messages from the
user chat queue, queries the knowledge base and builds a prompt for the LLM.


## Librarian
The librarian is responsible for getting the knowledge base data into the vector
database. It runs at startup, recreating the data set that is to be used for the
retrieval part of the system.


## Archivist
The archivist, like the librarian, adds data to the vector database. It reads
the live chat data and pushes that into the vector database as additional
reference.

The archivist listens on the message queue for chat messages. 


## Ollama LLM Runtime
We use [Ollama](https://ollama.com/) as the model run-time. Ollama makes it easy
to manage multiple models, without having to handle large model files. It also
solves the need for registration on all kinds of sites. Ollama will just pull
the model in and cache it locally.

In order for Ollama to be able to use the system's GPU (only works on Linux),
install
[NVidea's Container Toolkit](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image)
first. This must run on the Docker host and not inside a container, hence the
need to do a separate installation.

If you get the error `Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]`, you may have forgotten to run the [configuration step of the NVIDIA Container Toolkit installation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuration).

Unfortunately, this ends an with error that I have so far failed to resolve:
`Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error running hook #0: error running hook: exit status 1, stdout: , stderr: Auto-detected mode as 'legacy'
nvidia-container-cli: initialization error: load library failed: libnvidia-ml.so.1: cannot open shared object file: no such file or directory: unknown`

Maybe try: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html ?

See also:
- [Turn on GPU access with Docker Compose](https://docs.docker.com/compose/gpu-support/)
- [Installing the NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)


## ChromaDB Vector Database
The vector database takes care of embedding and semantic search on the knowledge
base library.

Rag doll uses [Chroma DB](https://www.trychroma.com/), being lightweigth and
easy to interface with.

See also [Running Chroma](https://cookbook.chromadb.dev/running/running-chroma/#docker).


## RabbitMQ Message Queueing
In order to separate the Slack and WhatsApp bots, we use message queues. This
allows us to organise and scale workloads, while having each component have only
a single responsibility.

### Queue Message Format

user message:
|---|---|---|
|field|data type|description|
|`id`       | string                                 | Message identification number as the originating platform knows it. |
|`timestamp`| ISO8601 UTC                            | Message timestamp as the originating platform knows it. |
|`platform` | enum: `SLACK`/`WHATSAPP`/`SMS`/`VOICE` | Originating platform. Intended to be able to parse the platform-specific fields. |
|`from`     | platform-specific address              | Enough information for the originating platform to be able to route a reply to this message to where the user expects it. |
|`text`     | UTF-8 string                           | The text as provided by the user. |
|---|---|---|

from field (where `platform` equals `SLACK`):

