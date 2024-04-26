import os
import time
import logging
import chromadb
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)


CHROMADB_HOST = os.getenv('CHROMADB_HOST')
CHROMADB_PORT = os.getenv('CHROMADB_PORT')
CHROMADB_COLLECTION = os.getenv('CHROMADB_COLLECTION')

# Connect to ChromaDB. ChromaDB takes a second or so to start, so we have a
# crude retry loop. Once connected. we clear the collection and recreate it from
# the Apache Parquet file provided.

chromadb_client = None

while chromadb_client == None:
    try:
        print(f"trying http://{CHROMADB_HOST}:{CHROMADB_PORT}/{CHROMADB_COLLECTION}...")
        chromadb_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
        chat_history = chromadb_client.create_collection(name=CHROMADB_COLLECTION)
    except Exception as e:
        print(f"unable to connect to http://{CHROMADB_HOST}:{CHROMADB_PORT}, retrying...: {e}")
        chromadb_client = None
        time.sleep(1)


def add_message_to_chroma(id, text, medium, from, country, to, language, timestamp):
    chat_history.add(
        documents=[text],
        metadatas=[{COL_MEDOIUM: medium, COL_FROM: from, COL_COUNTRY: country, COL_TO: to, COL_LANGUAGE: language, COL_TIMESTAMP: timestamp}],
        ids=[f"{id}"]
    )


# --- Connect to MQTT

client_id = "archivist"
mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT"))
mqtt_user = os.getenv("MQTT_USER")
mqtt_pass = os.getenv("MQTT_PASS")

def on_connect(client, userdata, flags, reason_code, properties=None):
    logging.info("on_connect: {}".format(mqtt.connack_string(reason_code)))
    client.publish(
        "health/" + client._client_id.decode("utf-8"),
        payload="connected",
        retain=True,
        qos=1,
    )

    if reason_code == mqtt.CONNACK_ACCEPTED:
        client.subscribe("roofpi/io/#", options=mqtt.SubscribeOptions(qos=1))


def on_disconnect(client, userdata, reason_code, properties=None):
    logging.info("on_disconnect: {}".format(mqtt.error_string(reason_code)))



def on_message(client, userdata, msg):
    # logging.info("on_message: {} {}".format(msg.topic, msg.payload.decode('utf-8')))
    
# --- --- filter unwanted: i.e. non-human messages ... Can we reconstruct a complete chat from the database? Does Chroma allow for basic queries or not? If not: where do we put the messages?

# --- --- decide: do we filter on Extension Officer answers only, or is that a
#         job for curators? What is the exact process of collecting, curating
#         and making searchable answers? For now, we err on the side of
#         simplicity: just put everything into the vector database.
# --- --- decide: how do we keep track of what chunks in the vector database
#         have been used / up/downvoted after retrieval?
# --- --- decide: how do we deal with privacy? We are handling messages that are
#         perceived as private.

# --- --- assemble key: reuse message key or just do uuid or incrementing

# --- --- assemble metadata:
#             medium (whatsapp/Slack/SMS/USSD).
#             from channel / from user / from phone
#             country of origin ISO 3166
#             to channel / to user / to phone
#             detected language ISO 3166 (or LOCALE-style?)
#             UTC timestamp

# --- --- put record into vector database

    add_message_to_chroma(id, text, medium, from, country, to, language, timestamp)


client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
client.enable_logger(logging.getLogger(__name__))

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.will_set("health/" + client_id, payload="lost", retain=True, qos=1)
client.username_pw_set(mqtt_user, mqtt_pass)
client.connect(mqtt_host, mqtt_port)

client.loop_forever()

