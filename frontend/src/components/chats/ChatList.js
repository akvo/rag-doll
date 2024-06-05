"use client";

import ChatTabs from "./ChatTabs";
import { useChatDispatch } from "@/context/ChatContextProvider";

const numbers = Array.from({ length: 10 }, (_, index) => index + 1);

const ChatList = () => {
  const chatDispatch = useChatDispatch();

  const handleOnClickChat = (id) => {
    chatDispatch({
      type: "UPDATE",
      payload: {
        clientId: id,
      },
    });
  };

  return (
    <div className="w-full bg-white p-4 overflow-y-scroll flex-shrink-0">
      <div className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200">
        <div className="mx-auto p-4">
          <div className="flex items-center space-x-2 mb-4">
            <h2 className="text-xl font-semibold">Chats</h2>
          </div>
          <div>
            <input
              type="text"
              placeholder="Search..."
              className="w-full px-4 py-2 border rounded"
            />
          </div>
        </div>
      </div>

      <div className="my-32 w-full">
        {/* Chat List */}
        <div className="bg-white overflow-hidden">
          {numbers.map((x) => (
            <div
              key={x}
              className="p-4 border-b border-gray-200 cursor-pointer"
              onClick={(x) => handleOnClickChat(x)}
            >
              <div className="flex items-center">
                <img
                  src="https://via.placeholder.com/40"
                  alt="User Avatar"
                  className="rounded-full mr-4"
                />
                <div>
                  <h3 className="text-lg font-semibold">Friend {x}</h3>
                  <p className="text-gray-600">Last message...</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ChatTabs />
    </div>
  );
};

export default ChatList;
