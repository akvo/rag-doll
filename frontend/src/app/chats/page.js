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

  // Handle socketio
  useEffect(() => {
    socket.connect();

    function onConnect() {
      console.info("FE Connected");
    }

    function onDisconnect(reason) {
      console.info(`FE Disconnected: ${reason}`);
      socket.connect();
    }

    function onChats(value, callback) {
      console.info(value, "socket chats");
      try {
        if (value) {
          const selectedClient = clients.find(
            (c) =>
              c.phone_number === value.conversation_envelope.client_phone_number
          );
          setReloadChatList(!selectedClient);

          // to handle show & loading whisper
          setWhisperChats((prev) => [
            ...prev.filter(
              (p) =>
                p.clientPhoneNumber !==
                value.conversation_envelope.client_phone_number
            ),
            {
              clientPhoneNumber:
                value.conversation_envelope.client_phone_number,
              message: null,
              timestamp: null,
              loading: true,
            },
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

        if (callback) {
          callback({ success: true, message: "Message received by FE" });
        }
      } catch (err) {
        if (callback) {
          callback({ success: false, message: "Message not received by FE" });
        }
      }
    }

    function onWhisper(value, callback) {
      console.info(value, "socket whisper");
      try {
        if (value) {
          setWhisperChats((prev) => {
            return prev.map((p) => {
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
              return prev;
            });
          });

          if (callback) {
            callback({ success: true, message: "Whisper received by FE" });
          }
        }
      } catch (err) {
        if (callback) {
          callback({ success: false, message: "Whisper not received by FE" });
        }
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
  }, [clients, clientPhoneNumber]);

  // handle on click notification
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
          whisperChats={whisperChats}
          setWhisperChats={setWhisperChats}
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
