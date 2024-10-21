"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useChatDispatch } from "@/context/ChatContextProvider";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { api } from "@/lib";
import { deleteCookie } from "@/lib/cookies";
import { formatChatTime, trimMessage } from "@/utils/formatter";
import ChatHeader from "./ChatHeader";
import Image from "next/image";
import { renderTextForMediaMessage } from "@/app/chats/page";
import FloatingPlusButton from "./FloatingPlusButton";
import Loading from "@/app/loading";
import { ChatStatusEnum, SenderRoleEnum } from "./ChatWindow";

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
  const [chatItems, setChatItems] = useState(initialChatItems);
  const [offset, setOffset] = useState(0);
  const limit = 10;
  const [loading, setLoading] = useState(true);

  const chatListRef = useRef(null);

  const handleOnClickChat = ({ client_id, name, phone_number }) => {
    chatDispatch({
      type: "UPDATE",
      payload: {
        clientId: client_id,
        clientName: name,
        clientPhoneNumber: phone_number,
      },
    });
  };

  const loadMoreChats = () => {
    setOffset((prevOffset) => prevOffset + limit);
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    const res = await api.get(`chat-list?limit=${limit}&offset=${offset}`);
    if (res.status === 200) {
      let resData = await res.json();
      resData = resData?.chats
        ? {
            ...resData,
            chats: resData.chats.filter((c) => c.last_message),
          }
        : resData;
      setClients((prev) =>
        resData.chats.map((c) => ({
          ...c.chat_session,
          last_message_created_at: c.last_message.created_at,
          message_ids:
            prev.find((p) => c.chat_session.client_id === p.client_id)
              ?.message_ids || [],
        }))
      );
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
      setLoading(false);
    }
    if (res.status === 401 || res.status === 403) {
      userDispatch({
        type: "DELETE",
      });
      authDispatch({ type: "DELETE" });
      deleteCookie("AUTH_TOKEN");
      setLoading(false);
      router.replace("/login");
    } else {
      setLoading(false);
    }
  }, [offset, authDispatch, router, setClients, userDispatch]);

  useEffect(() => {
    fetchData();
  }, [offset, fetchData]);

  useEffect(() => {
    if (reloadChatList) {
      fetchData();
      setReloadChatList(false);
    }
  }, [reloadChatList, fetchData, setReloadChatList]);

  // Handle infinite scroll
  useEffect(() => {
    const chatListRefTemp = chatListRef.current;
    const handleScroll = () => {
      if (chatListRefTemp) {
        const { scrollTop, scrollHeight, clientHeight } = chatListRefTemp;
        if (scrollTop + clientHeight >= scrollHeight - 5) {
          loadMoreChats();
        }
      }
    };

    chatListRefTemp?.addEventListener("scroll", handleScroll);
    return () => {
      chatListRefTemp?.removeEventListener("scroll", handleScroll);
    };
  }, []);

  // Update last message for incoming message
  useEffect(() => {
    if (newMessage.length) {
      setChatItems((prev) => {
        const updatedChatItems = prev.chats.map((chat) => {
          const findNewMessage = newMessage.find((nm) => {
            // message deduplication
            const isNewMessage =
              new Date(nm.conversation_envelope.timestamp) >
              new Date(chat.last_message.created_at);
            return (
              nm.conversation_envelope.client_phone_number ===
                chat.chat_session.phone_number && isNewMessage
            );
          });
          if (findNewMessage) {
            // handle message count
            const isUnread =
              findNewMessage.conversation_envelope.status ===
              ChatStatusEnum.UNREAD;
            const isAssistant =
              findNewMessage.conversation_envelope.sender_role ===
              SenderRoleEnum.ASSISTANT;
            const prevCount = chat?.unread_message_count || 0;
            return {
              ...chat,
              last_message: {
                ...chat.last_message,
                created_at: findNewMessage.conversation_envelope.timestamp,
                message: findNewMessage.body,
              },
              unread_assistant_message: isAssistant && isUnread,
              unread_message_count:
                !isAssistant && isUnread ? prevCount + 1 : prevCount,
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

  return (
    <div
      className="w-full h-screen bg-white overflow-y-scroll flex-shrink-0"
      ref={chatListRef}
    >
      <ChatHeader />
      {loading ? (
        <Loading />
      ) : (
        <>
          <div className="pt-20 pb-24 w-full">
            {/* Chat List */}
            <div className="bg-white overflow-hidden px-2">
              {chatItems.chats
                .filter((c) => c.last_message)
                .map(
                  ({
                    chat_session,
                    last_message,
                    unread_assistant_message,
                    unread_message_count,
                  }) => (
                    <div
                      key={`chat-list-${chat_session.id}`}
                      className="p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition"
                      onClick={() => handleOnClickChat(chat_session)}
                    >
                      <div className="flex items-center">
                        <Image
                          src="/images/bg-login-page.png"
                          alt="User Avatar"
                          className="rounded-full w-12 h-12 mr-4 bg-gray-300"
                          height={12}
                          width={12}
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
                          <div className="flex items-center">
                            <div className="flex-1">
                              {last_message.message?.trim() ? (
                                <p className="text-gray-600 text-sm">
                                  {trimMessage(last_message.message)}
                                </p>
                              ) : (
                                renderTextForMediaMessage({
                                  type: last_message?.media?.type,
                                })
                              )}
                            </div>
                            {unread_assistant_message ||
                            unread_message_count ? (
                              <div className="flex space-x-1 items-center justify-center">
                                {unread_assistant_message ? (
                                  <div className="w-5 h-5 bg-blue-300 rounded-full p-2">
                                    &nbsp;
                                  </div>
                                ) : (
                                  ""
                                )}
                                {unread_message_count > 0 ? (
                                  <div className="w-5 h-5 bg-green-600 rounded-full text-white flex items-center justify-center text-xs p-2">
                                    {unread_message_count}
                                  </div>
                                ) : (
                                  ""
                                )}
                              </div>
                            ) : (
                              ""
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                )}
            </div>
          </div>
          <FloatingPlusButton />
        </>
      )}
    </div>
  );
};

export default ChatList;
