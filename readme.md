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

## Slack Bot
The Slack bot is the first interface that can be used to chat with the rag doll.
Slack is a little more convenient to use than WhatsApp and it does mostly the
same. Good enough for a demo.

Most of the Slack interface code was taken from
[Python Slack Bot](https://www.youtube.com/playlist?list=PLzMcBGfZo4-kqyzTzJWCV6lyK-ZMYECDc)
by [Tech with Tim](https://www.youtube.com/@TechWithTim).

## Librarian
The librarian is responsible for getting the knowledge base data into the vector
database. It runs at startup, recreating the data set that is to be used for the
retrieval part of the system.

## Archivist
The archivist, like the librarian, adds data to the vector database. It reads
the live chat data and pushes that into the vector database as additional
reference.

## Vector Database
The vector database takes care of embedding and semantic search on the knowledge
base library.

Rag doll uses [Chroma DB](https://www.trychroma.com/), being lightweigth and
easy to interface with.

See also [Running Chroma](https://cookbook.chromadb.dev/running/running-chroma/#docker).

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
