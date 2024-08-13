"use client";

import { useState, useEffect, useRef } from "react";
import { useChatDispatch } from "@/context/ChatContextProvider";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { api } from "@/lib";
import { deleteCookie } from "@/lib/cookies";
import { formatChatTime } from "@/utils/formatter";

const initialChatItems = { total_chats: 0, chats: [], limit: 10, offset: 0 };

const ChatList = () => {
  const router = useRouter();
  const userDispatch = useUserDispatch();
  const authDispatch = useAuthDispatch();
  const chatDispatch = useChatDispatch();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [chatItems, setChatItems] = useState(initialChatItems);
  const [offset, setOffset] = useState(0);
  const limit = 10;

  const chatListRef = useRef(null);
  const dropdownRef = useRef(null);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleOnClickChat = ({ id, name, phone_number }) => {
    chatDispatch({
      type: "UPDATE",
      payload: {
        clientId: id,
        clientName: name,
        clientPhoneNumber: phone_number,
      },
    });
  };

  const handleOnClickSettings = () => {
    router.push("/settings");
  };

  const loadMoreChats = () => {
    setOffset((prevOffset) => prevOffset + limit);
  };

  useEffect(() => {
    const fetchData = async () => {
      const res = await api.get(`chat-list?limit=${limit}&offset=${offset}`);
      if (res.status === 200) {
        const resData = await res.json();
        setChatItems((prev) => ({
          ...prev,
          chats: [...prev.chats, ...resData.chats].filter(
            (value, index, self) =>
              index ===
              self.findIndex(
                (t) => t.chat_session.id === value.chat_session.id,
              ),
          ),
          limit: prev.limit,
          offset: resData.offset,
        }));
      }
      if (res.status === 401 || res.status === 403) {
        userDispatch({
          type: "DELETE",
        });
        authDispatch({ type: "DELETE" });
        deleteCookie("AUTH_TOKEN");
        router.replace("/login");
      }
    };
    fetchData();
  }, [offset]);

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
          {chatItems.chats.map(({ chat_session, last_message }) => (
            <div
              key={`chat-list-${chat_session.id}`}
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
                      {chat_session.name || chat_session.phone_number}
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
