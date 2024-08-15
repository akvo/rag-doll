"use client";

import {
  useRef,
  useState,
  useEffect,
  useLayoutEffect,
  useCallback,
  useMemo,
} from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { socket, api } from "@/lib";
import { formatChatTime, generateMessage } from "@/utils/formatter";
import { v4 as uuidv4 } from "uuid";
import Whisper from "./Whisper";
import MarkdownRenderer from "./MarkdownRenderer";

const SenderRoleEnum = {
  USER: "user",
  CLIENT: "client",
  ASSISTANT: "assistant",
  SYSTEM: "system",
};

const UserChat = ({ message, timestamp }) => (
  <div className="flex mb-4 justify-end">
    <div className="relative bg-green-500 text-white p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
      <div className="absolute bottom-0 right-0 w-0 h-0 border-t-8 border-t-green-500 border-r-8 border-r-transparent border-b-0 border-l-8 border-l-transparent transform -translate-x-1/2 translate-y-1/2"></div>
      {message?.split("\n")?.map((line, index) => (
        <MarkdownRenderer
          index={`user-${index}`}
          content={line}
          className={`prose-headings:text-white prose-strong:text-white prose-p:text-white prose-a:text-white prose-li:text-white prose-ol:text-white prose-ul:text-white prose-code:text-white text-white`}
        />
      ))}
      <p className="text-right text-xs text-gray-200 mt-2">
        {formatChatTime(timestamp)}
      </p>
    </div>
  </div>
);

const ClientChat = ({ message, timestamp }) => (
  <div className="flex mb-4">
    <div className="relative bg-white p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
      <div className="absolute bottom-0 left-0 w-0 h-0 border-t-8 border-t-white border-l-8 border-l-transparent border-b-0 border-r-8 border-r-transparent transform translate-x-1/2 translate-y-1/2"></div>
      {message?.split("\n")?.map((line, index) => (
        <MarkdownRenderer index={`client-${index}`} content={line} />
      ))}
      <p className="text-right text-xs text-gray-400 mt-2">
        {formatChatTime(timestamp)}
      </p>
    </div>
  </div>
);

const ChatWindow = ({
  chats,
  setChats,
  aiMessages,
  setAiMessages,
  loadingWhisper,
  showWhisper,
  setShowWhisper,
}) => {
  const chatContext = useChatContext();
  const chatDispatch = useChatDispatch();

  const { clientId, clientName, clientPhoneNumber } = chatContext;

  const textareaRef = useRef(null);
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);

  const scrollToLastMessage = useCallback(() => {
    const messagesContainer = document.getElementById("messagesContainer");
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, []);

  // Load previous chats from /api/chat-details/{clientId}
  useEffect(() => {
    async function fetchChats() {
      try {
        const res = await api.get(`/chat-details/${clientId}`);
        const data = await res.json();
        setChatHistory(data.messages);
        scrollToLastMessage();
      } catch (error) {
        console.error(error);
      }
    }
    fetchChats();
  }, [clientId, scrollToLastMessage]);

  // Trigger on chats change to scroll to the bottom
  useLayoutEffect(() => {
    scrollToLastMessage();
  }, [chats, scrollToLastMessage]);

  const handleInput = () => {
    const textarea = textareaRef.current;
    const maxHeight = 250;
    textarea.style.height = "auto"; // Reset height to auto
    textarea.style.height =
      textarea.scrollHeight <= maxHeight
        ? `${textarea.scrollHeight}px`
        : `${maxHeight}px`; // Set height based on scroll height
  };

  const handleChange = (event) => {
    setMessage(event.target.value);
  };

  const handleOnClickBack = () => {
    chatDispatch({
      type: "CLEAR",
    });
  };

  const handleSend = () => {
    if (message.trim()) {
      let chatBreakdown = {};
      const lastChat = chats.slice(-1)[0];
      if (lastChat && lastChat?.conversation_envelope) {
        chatBreakdown = {
          ...lastChat,
          ...lastChat.conversation_envelope,
        };
      } else {
        chatBreakdown = {
          message_id: uuidv4(),
          platform: "WHATSAPP",
        };
      }
      const chatPayload = generateMessage({
        ...chatBreakdown,
        client_phone_number: clientPhoneNumber,
        sender_role: SenderRoleEnum.USER,
        body: message,
        transformation_log: null,
      });
      setChats((previous) => [...previous, chatPayload]);
      socket.timeout(5000).emit("chats", chatPayload);
      setMessage(""); // Clear the textarea after sending
      textareaRef.current.style.height = "auto"; // Reset the height after sending
    }
  };

  const renderChatHistory = useMemo(() => {
    return chatHistory.map((c, ci) => {
      if (c.sender_role === SenderRoleEnum.USER) {
        return (
          <UserChat
            key={`user-history-${ci}`}
            message={c.message}
            timestamp={c.created_at}
          />
        );
      }
      if (c.sender_role === SenderRoleEnum.CLIENT) {
        return (
          <ClientChat
            key={`client-history-${ci}`}
            message={c.message}
            timestamp={c.created_at}
          />
        );
      }
    });
  }, [chatHistory]);

  const renderChats = useMemo(() => {
    return chats
      .filter(
        (chat) =>
          chat.conversation_envelope.client_phone_number === clientPhoneNumber
      )
      .map((c, ci) => {
        if (c?.conversation_envelope?.sender_role === SenderRoleEnum.USER) {
          return (
            <UserChat
              key={`user-${ci}`}
              message={c.body}
              timestamp={c.conversation_envelope.timestamp}
            />
          );
        }
        if (c?.conversation_envelope?.sender_role === SenderRoleEnum.CLIENT) {
          return (
            <ClientChat
              key={`client-${ci}`}
              message={c.body}
              timestamp={c.conversation_envelope.timestamp}
            />
          );
        }
      });
  }, [chats]);

  return (
    <div className="flex flex-col w-full h-screen bg-gray-200">
      {/* Chat Header */}
      <div className="flex items-center p-4 bg-white border-b">
        <div className="mr-4">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-6 h-6 cursor-pointer"
            onClick={handleOnClickBack}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 19.5 8.25 12l7.5-7.5"
            />
          </svg>
        </div>

        <img
          src="https://via.placeholder.com/40"
          alt="User Avatar"
          className="rounded-full mr-4 w-12"
        />

        <div>
          <h3 className="text-lg font-semibold">
            {clientName || clientPhoneNumber}
          </h3>
          <p className="text-sm text-gray-600">Online</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex flex-col h-3/4">
        {/* User Messages */}
        <div
          id="messagesContainer"
          className="flex-1 p-4 overflow-auto border-b"
        >
          {renderChatHistory()}
          {renderChats()}
        </div>

        {/* AI Messages */}
        <Whisper
          aiMessages={aiMessages}
          setAiMessages={setAiMessages}
          loadingWhisper={loadingWhisper}
          showWhisper={showWhisper}
          setShowWhisper={setShowWhisper}
        />
      </div>

      {/* TextArea */}
      <div className="flex p-4 bg-white border-t items-center fixed bottom-16 w-full z-20">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onInput={handleInput}
          placeholder="Type a message..."
          className="w-full px-4 py-2 border rounded-lg resize-none overflow-auto"
          rows={1}
        />
        <button
          onClick={handleSend}
          className="ml-4 bg-green-500 hover:bg-green-600 text-white p-3 rounded-full focus:outline-none"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="size-4"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
