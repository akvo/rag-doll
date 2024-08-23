"use client";

import ChatTabButton from "./ChatTabButton";
import { useChatContext } from "@/context/ChatContextProvider";

const ChatTabs = () => {
  const { clientPhoneNumber } = useChatContext();

  if (clientPhoneNumber) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-100 border-t border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-around items-center h-20">
          <ChatTabButton type="chats" />
          <ChatTabButton type="reference" />
          <ChatTabButton type="account" />
        </div>
      </div>
    </div>
  );
};

export default ChatTabs;
