"use client";

import { useEffect, useState } from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { ChatWindow, ChatList, ChatNotification } from "@/components";
import { socket } from "@/lib";

const Chats = () => {
  const chatDispatch = useChatDispatch();
  const { clientPhoneNumber } = useChatContext();
  const [chats, setChats] = useState([]);
  const [newMessage, setNewMessage] = useState([]);
  const [clients, setClients] = useState([]);
  const [reloadChatList, setReloadChatList] = useState(false);
  const [whisperChats, setWhisperChats] = useState([]);
  const [useWhisperAsTemplate, setUseWhisperAsTemplate] = useState(false);

  // Reset chats state when clientPhoneNumber changes
  useEffect(() => {
    setChats([]);
  }, [clientPhoneNumber]);

  // Connect to socket on component mount and disconnect on unmount
  useEffect(() => {
    if (!socket.connected) {
      socket.connect();
    }

    const handleConnect = () => {
      console.info("FE Connected");
    };

    const handleDisconnect = (reason) => {
      console.info(`FE Disconnected: ${reason}`);
    };

    socket.on("connect", handleConnect);
    socket.on("disconnect", handleDisconnect);

    return () => {
      socket.off("connect", handleConnect);
      socket.off("disconnect", handleDisconnect);
      socket.disconnect(); // Disconnect socket when component unmounts
    };
  }, []);

  // Handle socket events
  useEffect(() => {
    const handleChats = (value, callback) => {
      if (value) {
        const selectedClient = clients.find(
          (c) =>
            c.phone_number === value.conversation_envelope.client_phone_number
        );
        setReloadChatList(!selectedClient);

        setWhisperChats((prev) => [
          ...prev.filter(
            (p) =>
              p.clientPhoneNumber !==
              value.conversation_envelope.client_phone_number
          ),
          {
            clientPhoneNumber: value.conversation_envelope.client_phone_number,
            message: null,
            timestamp: null,
            loading: true,
          },
        ]);
        setUseWhisperAsTemplate(false);

        setNewMessage((prev) => [
          ...prev.filter(
            (p) =>
              p.conversation_envelope.message_id !==
              value?.conversation_envelope?.message_id
          ),
          value,
        ]);

        if (clientPhoneNumber) {
          setChats((prev) => [...prev, value]);
        }

        if (callback) {
          callback({ success: true, message: "Message received by FE" });
        }
      }
    };

    const handleWhisper = (value, callback) => {
      if (value) {
        setUseWhisperAsTemplate(false);
        setWhisperChats((prev) =>
          prev.map((p) => {
            if (
              p.clientPhoneNumber ===
              value.conversation_envelope.client_phone_number
            ) {
              return {
                ...p,
                message: value.body,
                timestamp: value.conversation_envelope.timestamp,
                loading: false,
              };
            }
            return p;
          })
        );

        if (callback) {
          callback({ success: true, message: "Whisper received by FE" });
        }
      }
    };

    socket.on("chats", handleChats);
    socket.on("whisper", handleWhisper);

    return () => {
      socket.off("chats", handleChats);
      socket.off("whisper", handleWhisper);
    };
  }, [clients, clientPhoneNumber]);

  // Handle click notification
  const handleOnClickNotification = (sender) => {
    const selectedClient = clients.find((c) => c.phone_number === sender);
    if (selectedClient) {
      chatDispatch({
        type: "UPDATE",
        payload: {
          clientId: selectedClient.id,
          clientName: selectedClient.name || selectedClient.phone_number,
          clientPhoneNumber: selectedClient.phone_number,
        },
      });
    }
  };

  return (
    <div className="w-full h-full">
      <div className="absolute right-4 top-4 flex flex-col gap-2">
        {newMessage.map((nm, index) => {
          let showNotif = clientPhoneNumber
            ? nm?.conversation_envelope?.client_phone_number !==
              clientPhoneNumber
            : true;

          return (
            <ChatNotification
              key={`chat-notification-${index}`}
              visible={showNotif}
              setVisible={() =>
                setNewMessage((prev) =>
                  prev.filter(
                    (p) =>
                      p.conversation_envelope.message_id !==
                      nm?.conversation_envelope?.message_id
                  )
                )
              }
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
          whisperChats={whisperChats}
          setWhisperChats={setWhisperChats}
          useWhisperAsTemplate={useWhisperAsTemplate}
          setUseWhisperAsTemplate={setUseWhisperAsTemplate}
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
