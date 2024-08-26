"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useChatDispatch } from "@/context/ChatContextProvider";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { api } from "@/lib";
import { deleteCookie } from "@/lib/cookies";
import { formatChatTime, trimMessage } from "@/utils/formatter";

const initialChatItems = { chats: [], limit: 10, offset: 0 };

const ChatList = ({
  newMessage,
  setClients,
  reloadChatList,
  setReloadChatList,
}) => {
  const router = useRouter();
  const userDispatch = useUserDispatch();
  const authDispatch = useAuthDispatch();
  const chatDispatch = useChatDispatch();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [chatItems, setChatItems] = useState(initialChatItems);
  const [offset, setOffset] = useState(0);
  const limit = 10;

  const chatListRef = useRef(null);
  const dropdownRef = useRef(null);

  const handleOnClickChat = ({ id, name, phone_number }) => {
    chatDispatch({
      type: "UPDATE",
      payload: {
        clientId: id,
        clientName: name,
        clientPhoneNumber: phone_number,
      },
    });
  };

  const loadMoreChats = () => {
    setOffset((prevOffset) => prevOffset + limit);
  };

  const fetchData = useCallback(async () => {
    const res = await api.get(`chat-list?limit=${limit}&offset=${offset}`);
    if (res.status === 200) {
      const resData = await res.json();
      setClients(resData.chats.map((c) => c.chat_session));
      setChatItems((prev) => {
        const updatedChats = [...prev.chats, ...resData.chats].reduce(
          (acc, incomingChat) => {
            const existingChatIndex = acc.findIndex(
              (chat) => chat.chat_session.id === incomingChat.chat_session.id
            );

            if (existingChatIndex > -1) {
              // Update the existing chat if the incoming chat's last_read is more recent
              if (
                new Date(acc[existingChatIndex].chat_session.last_read) <=
                new Date(incomingChat.chat_session.last_read)
              ) {
                acc[existingChatIndex] = incomingChat;
              }
            } else {
              // Add the new chat if the chat session ID is unique
              acc.push(incomingChat);
            }

            return acc;
          },
          [...prev.chats]
        );

        // Sort the chats by the last_message's created_at date in descending order
        const sortedChats = updatedChats.sort(
          (a, b) =>
            new Date(b.last_message.created_at) -
            new Date(a.last_message.created_at)
        );

        return {
          ...prev,
          chats: sortedChats,
          limit: prev.limit,
          offset: resData.offset,
        };
      });
    }
    if (res.status === 401 || res.status === 403) {
      userDispatch({
        type: "DELETE",
      });
      authDispatch({ type: "DELETE" });
      deleteCookie("AUTH_TOKEN");
      router.replace("/login");
    }
  }, [offset]);

  useEffect(() => {
    fetchData();
  }, [offset, fetchData]);

  useEffect(() => {
    if (reloadChatList) {
      fetchData();
      setReloadChatList(false);
    }
  }, [reloadChatList]);

  // Handle infinite scroll
  useEffect(() => {
    const handleScroll = () => {
      if (chatListRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = chatListRef.current;
        if (scrollTop + clientHeight >= scrollHeight - 5) {
          loadMoreChats();
        }
      }
    };

    chatListRef?.current?.addEventListener("scroll", handleScroll);
    return () => {
      chatListRef?.current?.removeEventListener("scroll", handleScroll);
    };
  }, []);

  // Update last message for incoming message
  useEffect(() => {
    if (newMessage.length) {
      setChatItems((prev) => {
        const updatedChatItems = prev.chats.map((chat) => {
          const findNewMessage = newMessage.find(
            (nm) =>
              nm.conversation_envelope.client_phone_number ===
              chat.chat_session.phone_number
          );
          if (findNewMessage) {
            return {
              ...chat,
              last_message: {
                ...chat.last_message,
                created_at: findNewMessage.conversation_envelope.timestamp,
                message: findNewMessage.body,
              },
            };
          }
          return chat;
        });

        return {
          ...prev,
          chats: updatedChatItems,
        };
      });
    }
  }, [newMessage]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div
      className="w-full h-screen bg-white overflow-y-scroll flex-shrink-0"
      ref={chatListRef}
    >
      <div className="sticky top-0 left-0 right-0 bg-gray-100 z-10 px-2 border-b border-gray-100">
        <div className="mx-auto py-4 px-6">
          <div className="flex items-center justify-center h-16">
            <h2 className="text-xl text-akvo-green font-semibold">
              AGRICONNECT
            </h2>
          </div>
        </div>
      </div>

      <div className="pb-20 w-full">
        {/* Chat List */}
        <div className="bg-white overflow-hidden  px-2">
          {chatItems.chats.map(({ chat_session, last_message }) => (
            <div
              key={`chat-list-${chat_session.id}`}
              className="p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition"
              onClick={() => handleOnClickChat(chat_session)}
            >
              <div className="flex items-center">
                <img
                  src="https://via.placeholder.com/40"
                  alt="User Avatar"
                  className="rounded-full w-10 h-10 mr-4"
                />
                <div className="flex-1">
                  <div className="flex justify-between">
                    <h3 className="text-md font-semibold text-gray-800">
                      {chat_session.name || chat_session.phone_number}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {formatChatTime(last_message.created_at)}
                    </p>
                  </div>
                  <p className="text-gray-600 text-sm">
                    {trimMessage(last_message.message)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatList;
