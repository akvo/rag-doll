"use client";

import React, { useEffect, useMemo } from "react";
import { formatChatTime } from "@/utils/formatter";
import { renderTextForMediaMessage } from "@/app/chats/page";
import { trimMessage } from "@/utils/formatter";

const ChatNotification = ({ visible, setVisible, notification, onClick }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible();
    }, 2500);
    return () => clearTimeout(timer);
  }, [notification, setVisible]);

  const timestamp = useMemo(() => {
    if (!notification?.messages?.length) {
      return null;
    }
    const message = notification.messages[notification.messages.length - 1];
    const tm = message?.conversation_envelope?.timestamp;
    if (tm) {
      return tm;
    }
    return null;
  }, [notification]);

  if (!visible) return null;

  return (
    <div
      className={`max-w-sm p-4 bg-gray-800 opacity-75 text-white rounded-lg shadow-md cursor-pointer transition-all transform ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
      onClick={() => onClick(notification)}
      style={{ zIndex: 1000 }}
    >
      <p className="font-bold text-sm">{notification.sender}</p>
      {notification.messages.map((m, index) => (
        <div key={`notification-${index}`}>
          {m.body ? (
            <p className="mt-1">{trimMessage(m.body)}</p>
          ) : (
            renderTextForMediaMessage({
              type: m?.media?.[0]?.type,
            })
          )}
        </div>
      ))}
      {timestamp ? (
        <p className="text-right text-xs text-green-200 mt-2">
          {formatChatTime(timestamp)}
        </p>
      ) : (
        ""
      )}
    </div>
  );
};

export default ChatNotification;
