"use client";

import { useEffect, useState } from "react";
import { useChatContext } from "@/context/ChatContextProvider";
import { ChatWindow, ChatList } from "@/components";
import { socket } from "@/lib";

const Chats = () => {
  const { clientPhoneNumber } = useChatContext();
  const [chats, setChats] = useState([]);
  const [aiMessages, setAiMessages] = useState([]);
  const [newMessage, setNewMessage] = useState(null);

  // Handle socketio
  useEffect(() => {
    socket.connect();

    function onConnect() {
      console.info("FE Connected");
    }

    function onDisconnect() {
      console.info("FE Disconnected");
    }

    function onChats(value) {
      console.info(value, "socket chats");
      setNewMessage(value);
      setChats((previous) => [...previous, value]);
    }

    function onWhisper(value) {
      console.log(value, "socket whisper");
      if (value) {
        setAiMessages(() => [
          { body: value.body, date: value.conversation_envelope.timestamp },
        ]);
      }
    }

    socket.on("connect", onConnect);
    socket.on("chats", onChats);
    socket.on("whisper", onWhisper);
    socket.on("disconnect", onDisconnect);

    return () => {
      socket.off("connect", onConnect);
      socket.off("chats", onChats);
      socket.off("whisper", onWhisper);
      socket.off("disconnect", onDisconnect);
    };
  });

  return clientPhoneNumber ? (
    <ChatWindow
      chats={chats}
      setChats={setChats}
      aiMessages={aiMessages}
      setAiMessages={setAiMessages}
    />
  ) : (
    <ChatList newMessage={newMessage} />
  );
};

export default Chats;
