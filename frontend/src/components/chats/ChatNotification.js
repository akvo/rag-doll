"use client";

import React, { useState, useEffect } from "react";
import { formatChatTime } from "@/utils/formatter";

const ChatNotification = ({ sender, message, timestamp, onClick }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
    const timer = setTimeout(() => setVisible(false), 3000);
    return () => clearTimeout(timer);
  }, [message]);

  if (!visible) return null;

  return (
    <div
      className={`fixed right-4 top-4 max-w-xs md:max-w-sm p-4 bg-gray-800 opacity-75 text-white rounded-lg shadow-md cursor-pointer transition-all transform ${
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
