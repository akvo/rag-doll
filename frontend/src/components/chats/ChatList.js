"use client";

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
    <div className="w-full h-screen bg-white overflow-y-scroll flex-shrink-0">
      <div className="sticky top-0 left-0 right-0 bg-white border-b border-gray-200 z-10">
        <div className="mx-auto p-4">
          <div className="flex items-center space-x-2 mb-4">
            <h2 className="text-xl font-semibold">Chats</h2>
          </div>
          <div>
            <input
              type="text"
              placeholder="Search..."
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
        </div>
      </div>

      <div className="pt-2 pb-20 w-full">
        {/* Chat List */}
        <div className="bg-white overflow-hidden">
          {numbers.map((x) => (
            <div
              key={x}
              className="p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-100 transition"
              onClick={() => handleOnClickChat(x)}
            >
              <div className="flex items-center">
                <img
                  src="https://via.placeholder.com/40"
                  alt="User Avatar"
                  className="rounded-full w-10 h-10 mr-4"
                />
                <div className="flex-1">
                  <div className="flex justify-between">
                    <h3 className="text-lg font-semibold">Friend {x}</h3>
                    <p className="text-xs text-gray-500">10:00 AM</p>
                  </div>
                  <p className="text-gray-600 text-sm">Last message...</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatList;
