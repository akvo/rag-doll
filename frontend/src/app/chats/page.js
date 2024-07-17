"use client";

import { useEffect, useState } from "react";
import { useChatContext } from "@/context/ChatContextProvider";
import { ChatWindow, ChatList } from "@/components";
import { socket } from "@/lib";

const Chats = () => {
  const { clientPhoneNumber } = useChatContext();

  useEffect(() => {
    socket.connect();

    function onConnect() {
      console.log("FE Connected");
    }

    function onDisconnect() {
      console.log("FE Disconnected");
    }

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
    };
  });

  return clientPhoneNumber ? <ChatWindow /> : <ChatList />;
};

export default Chats;
