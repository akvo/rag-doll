# RAG Doll
Rag Doll is a chat-with-your-documents style Retrieval Augmented Generation
(RAG). Rag Doll is broken up into several containers, each with a single
responsibility (or as close to that as I could get).

There are many RAG implementations out there and I don't proclaim this to be
better than any of the others. What sets Rag Doll apart is the fact that it
makes all previous chats available to the user. This feature does come with the
downside that the chat is added to the knowledge base as fact. It will not have
been curated or reviewed before it comes available to use in future searches.
Rag Doll assumes good faith and good factual knowledge by all participants in
the chat.

The implementation is mostly Python, although the heavy lifting is done by
pre-trained machine learning models. You'll want to run this on something with a
decent GPU, or you will find this all to be very slow.

This repository is an implementation of a mostly-Python Retrieval Augmented
Generation (RAG) system, organised into several containers. By containerizing,
we can more easily upgrade and improve individual componetns.

This demo is purely for text data, we do not demo multi-modal at this time.
Maybe later, feel free to suggest a pull request. :-)

## Prerequisites
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
$ sudo systemctl restart docker
$ docker info --format '{{.LoggingDriver}}'
local
```


## Slack Bot
The Slack bot is the first interface that can be used to chat with the rag doll.
Slack is a little more convenient to use than WhatsApp and it does mostly the
same. Good enough for a demo.

Most of the Slack interface code was taken from
[Getting started with Bolt for Python](https://seratch.github.io/bolt-python/tutorial/getting-started).


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


## TODO

- https://medium.com/@ingridwickstevens/chat-with-your-audio-locally-a-guide-to-rag-with-whisper-ollama-and-faiss-6656b0b40a68
- image embeddings
- https://www.youtube.com/watch?v=u_N1t0CBuqA
- fine-tune chunking rules
- test lemmatised text vs text as written (but then I cannot chunk on period).
- add filename as column to parquet corpus
- figure out how to do id's on ChromaDB
- Figure out how to gracefully await Chroma starting instead of sleeping for a few seconds
- Need some way to retain and add to the collection, instead of recreating every time
- Need to figure out how to collect likes/dislikes and then attach these to the records in the vector database. By collecting these, useful answers should make it into the knowledge base and we can suppress bad answers.
- Devise a way to stream the response from the LLM, as it is slow. Perhaps chat.update? Does Bolt have that in an easy way?
- Add error handling, such that if there is a problem, Slackbot sends a message to an admin
