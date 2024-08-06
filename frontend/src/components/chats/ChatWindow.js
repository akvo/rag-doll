"use client";

import { useRef, useState, useEffect, useLayoutEffect, Fragment } from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { socket } from "@/lib";
import { generateMessage } from "@/utils/formatter";
import { v4 as uuidv4 } from "uuid";

const SenderRoleEnum = {
  USER: "user",
  CLIENT: "client",
  ASSISTANT: "assistant",
  SYSTEM: "system",
};

const ChatWindow = () => {
  const chatContext = useChatContext();
  const chatDispatch = useChatDispatch();

  const { clientName, clientPhoneNumber } = chatContext;

  const textareaRef = useRef(null);
  const [message, setMessage] = useState("");
  const [aiMessages, setAiMessages] = useState([]);
  const [chats, setChats] = useState([]);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    function onChats(value) {
      console.log(value, "socket chats");
      if (
        value.conversation_envelope.client_phone_number === clientPhoneNumber
      ) {
        setChats((previous) => [...previous, value]);
      }
    }
    socket.on("chats", onChats);

    return () => {
      socket.off("chats", onChats);
    };
  }, []);

  useEffect(() => {
    setTimeout(() => {
      setAiMessages([
        ...aiMessages,
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis eget sollicitudin augue. Curabitur quis risus ut nulla consectetur gravida. Nunc sit amet turpis tempor, rutrum mi vel, molestie purus.",
      ]);
    }, 2000);
  }, []);

  useLayoutEffect(() => {
    const messagesContainer = document.getElementById("messagesContainer");
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    // Trigger on chats change to scroll to the bottom
  }, [chats]);

  const handleInput = () => {
    const textarea = textareaRef.current;
    textarea.style.height = "auto"; // Reset height to auto
    textarea.style.height = `${textarea.scrollHeight}px`; // Set height based on scroll height
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
      console.log(chatPayload, "chatPayload");
      setChats((previous) => [...previous, chatPayload]);
      socket.timeout(5000).emit("chats", chatPayload);
      setMessage(""); // Clear the textarea after sending
      textareaRef.current.style.height = "auto"; // Reset the height after sending
    }
  };

  const handleCopy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1000);
    } catch (error) {
      console.error("Failed to copy text: ", error);
    }
  };

  const renderChatMessages = () => {
    return chats.map((c, ci) => {
      if (c?.conversation_envelope?.sender_role === SenderRoleEnum.USER) {
        return (
          <div key={`user-${ci}`} className="flex mb-4 justify-end">
            <div className="relative bg-green-500 text-white p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
              <div className="absolute bottom-0 right-0 w-0 h-0 border-t-8 border-t-green-500 border-r-8 border-r-transparent border-b-0 border-l-8 border-l-transparent transform -translate-x-1/2 translate-y-1/2"></div>
              <p>
                {c?.body?.split("\n")?.map((line, index) => (
                  <Fragment key={index}>
                    {line}
                    <br />
                  </Fragment>
                ))}
              </p>
              <p className="text-right text-xs text-gray-200 mt-2">
                {`10.${ci + 10} AM`}
              </p>
            </div>
          </div>
        );
      }
      if (c?.conversation_envelope?.sender_role === SenderRoleEnum.CLIENT) {
        return (
          <div key={`client-${ci}`} className="flex mb-4">
            <div className="relative bg-white p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
              <div className="absolute bottom-0 left-0 w-0 h-0 border-t-8 border-t-white border-l-8 border-l-transparent border-b-0 border-r-8 border-r-transparent transform translate-x-1/2 translate-y-1/2"></div>
              <p>
                {c?.body?.split("\n")?.map((line, index) => (
                  <Fragment key={index}>
                    {line}
                    <br />
                  </Fragment>
                ))}
              </p>
              <p className="text-right text-xs text-gray-400 mt-2">10:00 AM</p>
            </div>
          </div>
        );
      }
    });
  };

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
          {/* Reply message */}
          <div className="flex mb-4">
            <div className="relative bg-white p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
              <div className="absolute bottom-0 left-0 w-0 h-0 border-t-8 border-t-white border-l-8 border-l-transparent border-b-0 border-r-8 border-r-transparent transform translate-x-1/2 translate-y-1/2"></div>
              <p>Hello! Lorem ipsum sit dolor</p>
              <p className="text-right text-xs text-gray-400 mt-2">10:00 AM</p>
            </div>
          </div>
          {/* Sent message */}
          <div className="flex mb-4 justify-end">
            <div className="relative bg-green-500 text-white p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
              <div className="absolute bottom-0 right-0 w-0 h-0 border-t-8 border-t-green-500 border-r-8 border-r-transparent border-b-0 border-l-8 border-l-transparent transform -translate-x-1/2 translate-y-1/2"></div>
              <p>Lorem ipsum dolor sit amet.</p>
              <p className="text-right text-xs text-gray-200 mt-2">10:01 AM</p>
            </div>
          </div>
          {renderChatMessages()}
        </div>

        {/* AI Messages */}
        {aiMessages.length ? (
          <div className="flex-1 p-4 overflow-auto mb-2">
            <div className="relative bg-gray-100 h-full rounded-lg shadow-inner overflow-auto">
              <div className="flex justify-between sticky top-0 py-2 bg-gray-100 z-10 px-4">
                <div className="justify-start">Recommendations</div>
                <div className="flex justify-end">
                  <button onClick={() => setAiMessages([])}>
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
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="p-4">
                {aiMessages.map((aiMessage, index) => (
                  <div className="mb-4">
                    <div key={index} className="flex mb-2">
                      <div className="relative bg-blue-500 text-white p-4 rounded-lg shadow-lg w-full">
                        <p>{aiMessage}</p>
                        <p className="text-right text-xs text-gray-200 mt-2">
                          AI - {new Date().toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex">
                      <button onClick={() => handleCopy(aiMessage)}>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                          className="w-6 h-6"
                        >
                          <path
                            fillRule="evenodd"
                            d="M8 2a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2H8zm0 2h8v10H8V4zM4 8a2 2 0 012-2h1v2H6v10h8v-1h2v1a2 2 0 01-2 2H6a2 2 0 01-2-2V8z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                      <button>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                          className="w-6 h-6"
                        >
                          <path
                            fillRule="evenodd"
                            d="M12 4a8 8 0 00-8 8H2l3.5 3.5L9 12H6.7A5.3 5.3 0 1112 17.3a5.3 5.3 0 01-5.3-5.3h-2A7.3 7.3 0 0012 19.3a7.3 7.3 0 000-14.6z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    </div>
                    {copied ? <div>Copied!</div> : ""}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          ""
        )}
      </div>

      {/* Input */}
      <div className="flex p-4 bg-white border-t items-center fixed bottom-16 w-full">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onInput={handleInput}
          placeholder="Type a message..."
          className="w-full px-4 py-2 border rounded-lg resize-none overflow-hidden"
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
