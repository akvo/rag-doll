"use client";
import { useState } from "react";
import { useChatContext } from "@/context/ChatContextProvider";
import { ChatSidebar, ChatWindow } from "@/components";

const Chats = () => {
  const { clientId } = useChatContext();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Chat Sidebar */}
      <ChatSidebar isSidebarOpen={isSidebarOpen} />

      {/* Chat List */}
      <div
        className={`${
          isSidebarOpen ? "sm:w-3/4" : "sm:w-full"
        } md:w-1/4 bg-white p-4 overflow-y-scroll flex-shrink-0`}
      >
        <div className="flex items-center space-x-2 mb-4">
          <button
            onClick={toggleSidebar}
            className="text-black focus:outline-none"
          >
            <svg
              className="h-6 w-6 fill-current"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
            >
              <path d="M0 0h24v24H0z" fill="none" />
              <path d="M4 18h16c.55 0 1-.45 1-1s-.45-1-1-1H4c-.55 0-1 .45-1 1s.45 1 1 1zm0-5h16c.55 0 1-.45 1-1s-.45-1-1-1H4c-.55 0-1 .45-1 1s.45 1 1 1zM3 7c0 .55.45 1 1 1h16c.55 0 1-.45 1-1s-.45-1-1-1H4c-.55 0-1 .45-1 1z" />
            </svg>
          </button>
          <h2 className="text-xl font-semibold">Chats</h2>
        </div>
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search..."
            className="w-full px-4 py-2 border rounded"
          />
        </div>
        <ul>
          <li className="mb-4">
            <a
              href="#"
              className="flex items-center p-4 bg-gray-100 rounded hover:bg-gray-200"
            >
              <img
                src="https://via.placeholder.com/40"
                alt="User Avatar"
                className="rounded-full mr-4"
              />
              <div>
                <h3 className="text-lg font-semibold">Chat 1</h3>
                <p className="text-sm text-gray-600">Last message...</p>
              </div>
            </a>
          </li>
          {/* Repeat for other chats */}
        </ul>
      </div>

      {/* Chat Window */}
      {clientId ? <ChatWindow /> : ""}
    </div>
  );
};

export default Chats;
