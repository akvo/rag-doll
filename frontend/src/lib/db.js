import Dexie from "dexie";

const DATABASE_NAME = "agriconnect";
const DATABASE_VERSION = 2;
const db = new Dexie(DATABASE_NAME);

db.version(DATABASE_VERSION).stores({
  // Table to save undelivered messages from officers to farmers,
  // which will be resent once the socket connection is reestablished.
  messages: "++id, chat_session_id, message, sender_role, created_at",

  // Table to store the last received message timestamp from farmers to officers
  // for a 24-hour window.
  lastMessageTimestamp:
    "client_phone_number, chat_session_id, user_message_timestamp, client_message_timestamp",
});

const dbInstance = () => {
  return {
    messages: {
      add: async ({ chat_session_id, message, sender_role, created_at }) => {
        const res = await db.messages.add({
          chat_session_id,
          message,
          sender_role,
          created_at,
        });
        return res;
      },
      getAll: async () => {
        return await db.messages.toArray();
      },
      getById: async (id) => {
        return await db.messages.get(id);
      },
      delete: async (id) => {
        await db.messages.delete(id);
      },
    },
    lastMessageTimestamp: {
      addOrUpdate: async ({
        client_phone_number,
        chat_session_id,
        sender_role,
        created_at,
      }) => {
        const lastMessage = await db.lastMessageTimestamp.get(
          client_phone_number
        );

        let value = {
          user_message_timestamp: lastMessage?.user_message_timestamp || null,
          client_message_timestamp:
            lastMessage?.client_message_timestamp || null,
        };
        if (sender_role === "user") {
          value = {
            ...value,
            user_message_timestamp: created_at,
          };
        }
        if (sender_role === "client") {
          value = {
            ...value,
            client_message_timestamp: created_at,
          };
        }
        if (lastMessage) {
          // Update the existing last message
          const res = await db.lastMessageTimestamp.update(
            lastMessage.client_phone_number,
            { ...value }
          );
          return res; // returns the number of records updated (1 if successful)
        } else {
          // Add a new last message
          const res = await db.lastMessageTimestamp.add({
            client_phone_number,
            chat_session_id,
            ...value,
          });
          return res; // returns the id of the newly added record
        }
      },
      getByClientPhoneNumber: async (client_phone_number) => {
        return await db.lastMessageTimestamp.get(client_phone_number);
      },
    },
  };
};

const dbLib = dbInstance();

export default dbLib;
