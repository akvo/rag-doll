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
  const [newMessage, setNewMessage] = useState([]);
  const [clients, setClients] = useState([]);
  const [reloadChatList, setReloadChatList] = useState(false);
  const [showWhisper, setShowWhisper] = useState([]);
  const [loadingWhisper, setLoadingWhisper] = useState([]);

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

        // to handle show & loading whisper
        setShowWhisper((prev) => [
          ...new Set([
            ...prev,
            value.conversation_envelope.client_phone_number,
          ]),
        ]);
        setLoadingWhisper((prev) => [
          ...new Set([
            ...prev,
            value.conversation_envelope.client_phone_number,
          ]),
        ]);
        // EOL to handle show & loading whisper

        setNewMessage((previous) => [
          ...previous.filter(
            (p) =>
              p.conversation_envelope.message_id !==
              value?.conversation_envelope?.message_id
          ),
          value,
        ]);
      }
      // set chats from socket if chat window opened
      if (value && clientPhoneNumber) {
        setChats((previous) => [...previous, value]);
      }
    }

    function onWhisper(value) {
      console.info(value, "socket whisper");
      if (value) {
        setLoadingWhisper((prev) =>
          prev.filter(
            (p) => p !== value.conversation_envelope.client_phone_number
          )
        );
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
      <div className="absolute right-4 top-4 flex flex-col gap-2">
        {newMessage.map((nm, index) => {
          let showNotif = false;
          if (clientPhoneNumber) {
            showNotif =
              clientPhoneNumber &&
              nm?.conversation_envelope?.client_phone_number !==
                clientPhoneNumber
                ? true
                : false;
          } else {
            showNotif = true;
          }
          return (
            <ChatNotification
              key={`chat-notification-${index}`}
              visible={showNotif}
              setVisible={() => {
                setNewMessage((prev) =>
                  prev.filter(
                    (p) =>
                      p.conversation_envelope.message_id !==
                      nm?.conversation_envelope?.message_id
                  )
                );
              }}
              sender={nm?.conversation_envelope?.client_phone_number}
              message={nm?.body}
              timestamp={nm?.conversation_envelope?.timestamp}
              onClick={handleOnClickNotification}
              setNewMessage={setNewMessage}
            />
          );
        })}
      </div>
      {clientPhoneNumber ? (
        <ChatWindow
          chats={chats}
          setChats={setChats}
          aiMessages={aiMessages}
          setAiMessages={setAiMessages}
          loadingWhisper={loadingWhisper}
          showWhisper={showWhisper}
          setShowWhisper={setShowWhisper}
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
