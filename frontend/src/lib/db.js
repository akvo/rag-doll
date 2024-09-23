import Dexie from "dexie";

const DATABASE_NAME = "agriconnect";
const DATABASE_VERSION = 1;
const db = new Dexie(DATABASE_NAME);

db.version(DATABASE_VERSION).stores({
  messages: "++id, chat_session_id, message, sender_role, created_at",
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
  };
};

const dbLib = dbInstance();

export default dbLib;
