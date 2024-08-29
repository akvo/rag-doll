"use client";

import React, { useEffect } from "react";
import { formatChatTime } from "@/utils/formatter";

const ChatNotification = ({
  visible,
  setVisible,
  sender,
  message,
  timestamp,
  onClick,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible();
    }, 1500);
    return () => clearTimeout(timer);
  }, [message, setVisible]);

  if (!visible) return null;

  return (
    <div
      className={`max-w-sm p-4 bg-gray-800 opacity-75 text-white rounded-lg shadow-md cursor-pointer transition-all transform ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
      onClick={() => onClick(sender)}
      style={{ zIndex: 1000 }}
    >
      <p className="font-bold text-sm">{sender}</p>
      <p className="mt-1">{message}</p>
      <p className="text-right text-xs text-green-200 mt-2">
        {formatChatTime(timestamp)}
      </p>
    </div>
  );
};

export default ChatNotification;
