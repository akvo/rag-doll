"use client";
import { useState } from "react";
import { useChatContext } from "@/context/ChatContextProvider";

const Chats = () => {
  const chat = useChatContext();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`fixed md:relative ${
          isSidebarOpen ? "w-1/4" : "md:hidden"
        } bg-gray-800 text-white p-4 overflow-hidden transition-all duration-300`}
      >
        {/* Sidebar Header */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-2">
            <img
              src="https://via.placeholder.com/50"
              alt="User Avatar"
              className="rounded-full"
            />
            <div>
              <h2 className="text-lg font-semibold">Username</h2>
              <p className="text-sm">Status</p>
            </div>
          </div>
        </div>
        {/* Sidebar Navigation */}
        <nav>
          <ul>
            <li className="mb-2">
              <a
                href="#"
                className="flex items-center px-4 py-2 text-gray-200 hover:bg-gray-700 rounded"
              >
                <span>Chats</span>
              </a>
            </li>
            <li className="mb-2">
              <a
                href="#"
                className="flex items-center px-4 py-2 text-gray-200 hover:bg-gray-700 rounded"
              >
                <span>Contacts</span>
              </a>
            </li>
            <li className="mb-2">
              <a
                href="#"
                className="flex items-center px-4 py-2 text-gray-200 hover:bg-gray-700 rounded"
              >
                <span>Settings</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>

      {/* Chat List */}
      <div className="w-full md:w-1/4 bg-white p-4 overflow-y-scroll flex-shrink-0">
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
      <div className="w-full bg-gray-200 flex flex-col">
        {/* Chat Header */}
        <div className="flex items-center p-4 bg-white border-b">
          <img
            src="https://via.placeholder.com/40"
            alt="User Avatar"
            className="rounded-full mr-4"
          />
          <div>
            <h3 className="text-lg font-semibold">Chat 1</h3>
            <p className="text-sm text-gray-600">Online</p>
          </div>
        </div>
        {/* Messages */}
        <div className="flex-1 p-4 overflow-y-scroll">
          <div className="flex mb-4">
            <img
              src="https://via.placeholder.com/40"
              alt="User Avatar"
              className="rounded-full mr-4"
            />
            <div>
              <p className="bg-white p-4 rounded shadow">Hello!</p>
              <p className="text-sm text-gray-600 mt-1">10:00 AM</p>
            </div>
          </div>
          {/* Repeat for other messages */}
        </div>
        {/* Input */}
        <div className="p-4 bg-white border-t">
          <input
            type="text"
            placeholder="Type a message..."
            className="w-full px-4 py-2 border rounded"
          />
        </div>
      </div>
    </div>
  );
};

export default Chats;
