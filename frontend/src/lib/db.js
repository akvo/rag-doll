import Dexie from "dexie";

const DATABASE_NAME = "agriconnect";
const DATABASE_VERSION = 1;
const db = new Dexie(DATABASE_NAME);

db.version(DATABASE_VERSION).stores({
  // Table to save undelivered messages from officers to farmers,
  // which will be resent once the socket connection is reestablished.
  messages: "++id, chat_session_id, message, sender_role, created_at",

  // Table to store the last received message timestamp from farmers to officers
  // for a 24-hour window.
  lastMessage: "++id, chat_session_id, sender_role, created_at",
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
    lastMessage: {
      addOrUpdate: async ({ chat_session_id, sender_role, created_at }) => {
        const lastMessage = await db.lastMessage
          .where("chat_session_id")
          .equals(chat_session_id)
          .first();
        if (lastMessage) {
          // Update the existing last message
          const res = await db.lastMessage.update(lastMessage.id, {
            sender_role,
            created_at,
          });
          return res; // returns the number of records updated (1 if successful)
        } else {
          // Add a new last message
          const res = await db.lastMessage.add({
            chat_session_id,
            sender_role,
            created_at,
          });
          return res; // returns the id of the newly added record
        }
      },
      getByChatSessionId: async (chat_session_id) => {
        return await db.lastMessage
          .where("chat_session_id")
          .equals(chat_session_id)
          .first();
      },
    },
  };
};

const dbLib = dbInstance();

export default dbLib;
