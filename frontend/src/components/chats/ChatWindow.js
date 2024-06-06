"use client";

import { useRef, useState } from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";

const ChatWindow = () => {
  const chatContext = useChatContext();
  const chatDispatch = useChatDispatch();

  const textareaRef = useRef(null);
  const [message, setMessage] = useState("");
  const [aiMessages, setAiMessages] = useState([
    "AI suggested message...",
    <>
      Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis eget
      sollicitudin augue. Curabitur quis risus ut nulla consectetur gravida.
      Nunc sit amet turpis tempor, rutrum mi vel, molestie purus. Lorem ipsum
      dolor sit amet, consectetur adipiscing elit. In hac habitasse platea
      dictumst. Donec dignissim mi ut eros elementum fringilla. Phasellus
      maximus feugiat nunc. Aliquam erat volutpat. Cras dictum tortor bibendum
      velit dapibus, in rutrum mi porttitor. In malesuada odio at augue
      efficitur maximus. Nullam elementum est a sagittis consectetur. Nullam ac
      sem dolor. Pellentesque quis sagittis augue. Quisque lobortis sed eros ut
      dignissim. Curabitur fringilla hendrerit dui, vitae consequat dolor
    </>,
  ]);

  const handleInput = (event) => {
    const textarea = textareaRef.current;
    textarea.style.height = "auto"; // Reset height to auto
    textarea.style.height = `${textarea.scrollHeight}px`; // Set height based on scroll height
  };

  const handleChange = (event) => {
    setMessage(event.target.value);
  };

  const handleOnClickBack = () => {
    chatDispatch({
      type: "UPDATE",
      payload: {
        clientId: null,
      },
    });
  };

  const handleSend = () => {
    if (message.trim()) {
      // Implement your send message logic here
      setMessage(""); // Clear the textarea after sending
      textareaRef.current.style.height = "auto"; // Reset the height after sending
    }
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
          <h3 className="text-lg font-semibold">{`Chat ${chatContext?.clientId}`}</h3>
          <p className="text-sm text-gray-600">Online</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex flex-col h-3/4">
        {/* User Messages */}
        <div className="flex-1 p-4 overflow-auto border-b">
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
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis
                eget sollicitudin augue. Curabitur quis risus ut nulla
                consectetur gravida. Nunc sit amet turpis tempor, rutrum mi vel,
                molestie purus. Lorem ipsum dolor sit amet, consectetur
                adipiscing elit. In hac habitasse platea dictumst. Donec
                dignissim mi ut eros elementum fringilla. Phasellus maximus
                feugiat nunc. Aliquam erat volutpat. Cras dictum tortor bibendum
                velit dapibus, in rutrum mi porttitor. In malesuada odio at
                augue efficitur maximus. Nullam elementum est a sagittis
                consectetur. Nullam ac sem dolor. Pellentesque quis sagittis
                augue. Quisque lobortis sed eros ut dignissim. Curabitur
                fringilla hendrerit dui, vitae consequat dolor.
              </p>
              <p className="text-right text-xs text-gray-200 mt-2">10:01 AM</p>
            </div>
          </div>
        </div>

        {/* AI Messages */}
        <div className="flex-1 p-4 overflow-auto mb-2">
          <div className="bg-gray-100 p-4 h-full rounded-lg shadow-inner overflow-auto">
            {aiMessages.map((aiMessage, index) => (
              <div key={index} className="flex mb-4">
                <div className="relative bg-blue-500 text-white p-4 rounded-lg shadow-lg w-full">
                  <p>{aiMessage}</p>
                  <p className="text-right text-xs text-gray-200 mt-2">
                    AI - {new Date().toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
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
