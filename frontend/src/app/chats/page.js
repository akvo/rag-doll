"use client";

import { useEffect, useState } from "react";
import { useChatContext } from "@/context/ChatContextProvider";
import { ChatWindow, ChatList } from "@/components";
import { socket, api } from "@/lib";
import { getCookie } from "../(auth)/verify/[loginId]/util";

const Chats = () => {
  const { clientId } = useChatContext();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const setApiToken = async () => {
      const token = await getCookie("AUTH_TOKEN");
      api.setToken(token);
    };
    setApiToken();
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

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

  if (loading) {
    return "";
  }

  return clientId ? <ChatWindow /> : <ChatList />;
};

export default Chats;
