"use client";

import { createContext, useContext, useEffect } from "react";
import { socket } from "@/lib";

const SocketContext = createContext();

export const SocketContextProvider = ({ children }) => {
  useEffect(() => {
    socket.connect();

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <SocketContext.Provider value={socket}>{children}</SocketContext.Provider>
  );
};

export const useSocket = () => useContext(SocketContext);

export default SocketContextProvider;
