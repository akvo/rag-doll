"use client";

import { useEffect, useState } from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { ChatWindow, ChatList, ChatNotification } from "@/components";
import { socket } from "@/lib";

const Chats = () => {
  const chatDispatch = useChatDispatch();
  const { clientPhoneNumber } = useChatContext();
  const [chats, setChats] = useState([]);
  const [aiMessages, setAiMessages] = useState([]);
  const [newMessage, setNewMessage] = useState(null);
  const [clients, setClients] = useState([]);
  const [reloadChatList, setReloadChatList] = useState(false);

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
        const findClient = clients.find(
          (c) =>
            c.phone_number === value.conversation_envelope.client_phone_number
        );
        setReloadChatList(!findClient);
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

  // handle on click notification
  const handleOnClickNotification = (sender) => {
    const findClient = clients.find((c) => c.phone_number === sender);
    console.log(findClient, clients);
    if (findClient) {
      chatDispatch({
        type: "UPDATE",
        payload: {
          clientId: findClient.id,
          clientName: findClient.name || findClient.phone_number,
          clientPhoneNumber: findClient.phone_number,
        },
      });
    }
  };

  return (
    <div className="w-full h-full">
      {newMessage &&
      newMessage?.conversation_envelope?.client_phone_number !==
        clientPhoneNumber ? (
        <ChatNotification
          sender={newMessage?.conversation_envelope?.client_phone_number}
          message={newMessage?.body}
          timestamp={newMessage?.conversation_envelope?.timestamp}
          onClick={handleOnClickNotification}
        />
      ) : (
        ""
      )}
      {clientPhoneNumber ? (
        <ChatWindow
          chats={chats}
          setChats={setChats}
          aiMessages={aiMessages}
          setAiMessages={setAiMessages}
        />
      ) : (
        <ChatList
          newMessage={newMessage}
          setClients={setClients}
          reloadChatList={reloadChatList}
          setReloadChatList={setReloadChatList}
        />
      )}
    </div>
  );
};

export default Chats;
