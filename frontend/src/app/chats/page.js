"use client";
import { useChatContext } from "@/context/ChatContextProvider";

const Chats = () => {
  const chat = useChatContext();
  console.log(chat);

  return <div>Chats</div>;
};

export default Chats;
