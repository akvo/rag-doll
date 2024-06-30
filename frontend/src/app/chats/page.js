"use client";
import { useChatContext } from "@/context/ChatContextProvider";
import { ChatWindow, ChatList } from "@/components";

const Chats = () => {
  const { clientId } = useChatContext();

  return clientId ? <ChatWindow /> : <ChatList />;
};

export default Chats;
