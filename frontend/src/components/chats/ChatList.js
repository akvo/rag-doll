"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useChatDispatch } from "@/context/ChatContextProvider";
import { useRouter } from "next/navigation";
import { api } from "@/lib";

function formatChatTime(timeString) {
  const date = new Date(timeString);
  const now = new Date();

  const diffInMilliseconds = now.getTime() - date.getTime();
  const diffInSeconds = Math.floor(diffInMilliseconds / 1000);

  // Define thresholds in seconds for different chat time formats
  const minute = 60;
  const hour = minute * 60;
  const day = hour * 24;

  if (diffInSeconds < 5) {
    return "Just now";
  } else if (diffInSeconds < minute) {
    return `${diffInSeconds} seconds ago`;
  } else if (diffInSeconds < hour) {
    const minutes = Math.floor(diffInSeconds / minute);
    return `${minutes} minutes ago`;
  } else if (now.getDate() === date.getDate()) {
    // Show time in HH:mm format if it's today
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  } else if (diffInSeconds < day * 2 && now.getDate() !== date.getDate()) {
    return "Yesterday";
  } else {
    // Use Intl.DateTimeFormat for localized date format
    const formatter = new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      hour12: true,
    });
    return formatter.format(date);
  }
}

const ChatList = () => {
  const router = useRouter();
  const chatDispatch = useChatDispatch();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [chatItems, setChatItems] = useState([]);
  const [page, setPage] = useState(1);
  const chatListRef = useRef(null);
  const dropdownRef = useRef(null);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleOnClickChat = ({ client_id }) => {
    chatDispatch({
      type: "UPDATE",
      payload: {
        clientId: client_id,
      },
    });
  };

  const handleOnClickSettings = () => {
    router.push("/settings");
  };

  const loadMoreChats = () => {
    setChatItems((prevChats) => [...prevChats]);
    setPage((prevPage) => prevPage + 1);
  };

  useEffect(() => {
    const fetchData = async () => {
      const res = await api.get("chat-list");
      const resData = await res.json();
      if (res.status === 200) {
        setChatItems(resData);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      if (chatListRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = chatListRef.current;
        if (scrollTop + clientHeight >= scrollHeight - 5) {
          loadMoreChats();
        }
      }
    };

    chatListRef?.current?.addEventListener("scroll", handleScroll);
    return () => {
      chatListRef?.current?.removeEventListener("scroll", handleScroll);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div
      className="w-full h-screen bg-gray-100 overflow-y-scroll flex-shrink-0"
      ref={chatListRef}
    >
      <div className="sticky top-0 left-0 right-0 bg-white border-b border-gray-200 z-10">
        <div className="mx-auto p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Chats</h2>
            <div className="relative">
              <button
                className="p-2 text-gray-600 focus:outline-none"
                onClick={toggleDropdown}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 6h.01M12 12h.01M12 18h.01M12 6a.75.75 0 0 1-.75-.75H12a.75.75 0 0 1 0 1.5h-.01M12 12a.75.75 0 0 1-.75-.75H12a.75.75 0 0 1 0 1.5h-.01M12 18a.75.75 0 0 1-.75-.75H12a.75.75 0 0 1 0 1.5h-.01"
                  />
                </svg>
              </button>
              {isDropdownOpen && (
                <div
                  ref={dropdownRef}
                  className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-20 transition ease-out duration-100 transform opacity-100 scale-100 origin-top-right"
                >
                  <ul className="py-1">
                    <li
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                      onClick={handleOnClickSettings}
                    >
                      Settings
                    </li>
                    <li className="px-4 py-2 hover:bg-gray-100 cursor-pointer">
                      About
                    </li>
                  </ul>
                </div>
              )}
            </div>
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
          {chatItems.map(({ chat_session, last_message }) => (
            <div
              key={chat_session.id}
              className="p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition"
              onClick={() => handleOnClickChat(chat_session)}
            >
              <div className="flex items-center">
                <img
                  src="https://via.placeholder.com/40"
                  alt="User Avatar"
                  className="rounded-full w-10 h-10 mr-4"
                />
                <div className="flex-1">
                  <div className="flex justify-between">
                    <h3 className="text-lg font-semibold text-gray-800">
                      Friend {chat_session.client_id}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {formatChatTime(last_message.created_at)}
                    </p>
                  </div>
                  <p className="text-gray-600 text-sm">
                    {last_message.message}
                  </p>
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
