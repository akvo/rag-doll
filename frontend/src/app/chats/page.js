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
      if (value) {
        setNewMessage(value);
      }
      // set chats from socket if chat window opened
      if (value && clientPhoneNumber) {
        setChats((previous) => [...previous, value]);
      }
    }

    function onWhisper(value) {
      console.log(value, "socket whisper");
      if (value) {
        setAiMessages((prev) => [
          ...prev.filter(
            (p) =>
              p.conversation_envelope.client_phone_number !==
              value.conversation_envelope.client_phone_number
          ),
          value,
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
