"use client";

import { useEffect, useState } from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { useUserContext } from "@/context/UserContextProvider";
import {
  ChatWindow,
  ChatList,
  ChatNotification,
  PushNotifications,
} from "@/components";
import { socket, dbLib } from "@/lib";
import { PhotoIcon } from "@/utils/icons";

export const renderTextForMediaMessage = ({ type = "" }) => {
  const mediaType = type?.split("/")?.[0];
  switch (mediaType) {
    case "image":
      return (
        <div className="flex items-center text-gray-600 text-sm">
          <PhotoIcon />
          <div className="ml-2">Photo</div>
        </div>
      );
    default:
      return "Media";
  }
};

const Chats = () => {
  const chatDispatch = useChatDispatch();
  const { clientPhoneNumber } = useChatContext();
  const { phone_number: userPhoneNumber } = useUserContext();
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

  // handle check if selectedClient in local storage
  // then forward to related chat window
  useEffect(() => {
    const res = localStorage.getItem("selectedClient");
    if (res) {
      const selectedClient = JSON.parse(res);
      chatDispatch({
        type: "UPDATE",
        payload: {
          clientId: selectedClient.id,
          clientName: selectedClient.name || selectedClient.phone_number,
          clientPhoneNumber: selectedClient.phone_number,
        },
      });
      localStorage.removeItem("selectedClient");
    }
  }, [chatDispatch]);

  // Connect to socket on component mount and disconnect on unmount
  useEffect(() => {
    if (!socket.connected) {
      socket.connect();
    }

    const handleConnect = async () => {
      console.info("FE Connected");
      const messages = await dbLib.messages.getAll();
      messages.forEach(async ({ id, message }) => {
        try {
          const response = await socket
            .timeout(5000)
            .emitWithAck("chats", message);
          if (response?.success) {
            dbLib.messages.delete(id);
          }
        } catch (err) {
          console.info(`Failed to resend lost message: ${err}`);
        }
      });
    };

    const handleDisconnect = (reason, details) => {
      console.info(`FE Disconnected: ${reason}`);
      console.info("FE Disconnected", details);
    };

    socket.on("connect", handleConnect);
    socket.on("disconnect", handleDisconnect);

    socket.on("connect_error", (err) => {
      console.error("FE Connect_Error", err);
    });

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
        const isMediaMessage = value?.media?.length > 0;

        const selectedClient = clients.find(
          (c) =>
            c.phone_number === value.conversation_envelope.client_phone_number
        );
        setReloadChatList(!selectedClient);

        setWhisperChats((prev) => {
          const filteredWhisper = prev.filter(
            (p) =>
              p.clientPhoneNumber !==
              value.conversation_envelope.client_phone_number
          );
          return isMediaMessage
            ? filteredWhisper
            : [
                ...filteredWhisper,
                {
                  clientPhoneNumber:
                    value.conversation_envelope.client_phone_number,
                  message: null,
                  timestamp: null,
                  loading: true,
                },
              ];
        });
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
          // handle message deduplication
          setChats((prev) => {
            const findPrev = prev.find(
              (p) =>
                p.conversation_envelope.message_id ===
                value.conversation_envelope.message_id
            );
            if (findPrev) {
              return prev;
            }
            return [...prev, value];
          });
        }

        if (callback) {
          callback({ success: true, message: value });
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
                message_id: value.conversation_envelope.message_id,
                message: value.body,
                timestamp: value.conversation_envelope.timestamp,
                loading: false,
              };
            }
            return p;
          })
        );

        if (callback) {
          callback({ success: true, message: value });
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
      {/* Enable push notification */}
      <PushNotifications />
      <div className="absolute right-4 top-4 flex flex-col gap-2">
        {newMessage
          .filter((nm) => {
            // handle deduplication
            const findClient = clients.find(
              (c) =>
                c.phone_number ===
                nm?.conversation_envelope?.client_phone_number
            );

            // if populated chat is not empty, check message_id is in populated chat
            let isNewMessage = true;
            if (findClient?.message_ids?.length) {
              const isMessageInMessageIds = findClient.message_ids.find(
                (id) => id === nm.conversation_envelope.message_id
              );
              isNewMessage = isMessageInMessageIds ? false : true;
            } else {
              // check by date/timestamp
              isNewMessage =
                findClient && nm?.conversation_envelope?.timestamp
                  ? new Date(nm?.conversation_envelope?.timestamp) >
                    new Date(findClient?.last_message_created_at)
                  : true;
            }
            // eol handle deduplication

            return (
              nm?.conversation_envelope?.user_phone_number ===
                userPhoneNumber && isNewMessage
            );
          })
          .reduce((acc, nm) => {
            const existingNotification = acc.find(
              (n) => n.sender === nm.conversation_envelope.client_phone_number
            );
            if (existingNotification) {
              existingNotification.messages.push(nm);
            } else {
              acc.push({
                sender: nm.conversation_envelope.client_phone_number,
                messages: [nm],
              });
            }
            return acc;
          }, [])
          .map((notification, index) => (
            <ChatNotification
              key={`chat-notification-${index}`}
              visible={notification.sender !== clientPhoneNumber}
              setVisible={() =>
                setNewMessage((prev) =>
                  prev.filter(
                    (p) =>
                      p.conversation_envelope.message_id !==
                      notification.messages[0].conversation_envelope.message_id
                  )
                )
              }
              notification={notification}
              onClick={handleOnClickNotification}
            />
          ))}
      </div>
      {clientPhoneNumber ? (
        <ChatWindow
          chats={chats}
          setChats={setChats}
          whisperChats={whisperChats}
          setWhisperChats={setWhisperChats}
          useWhisperAsTemplate={useWhisperAsTemplate}
          setUseWhisperAsTemplate={setUseWhisperAsTemplate}
          setClients={setClients}
          clients={clients}
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
