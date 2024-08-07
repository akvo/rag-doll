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

const ChatMessages = ({ chats = [] }) => {
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

const AiMessages = ({ chats }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1000);
    } catch (error) {
      console.error("Failed to copy text: ", error);
    }
  };

  const handleReload = (text) => {
    const reloaded = aiMessages.map((item) =>
      item === text ? "Reloaded message..." : item
    );
    setAiMessages(reloaded);
  };

  return (
    <div className="flex-1 p-4 overflow-auto mb-2">
      <div className="relative bg-gray-100 h-full rounded-lg shadow-inner overflow-auto">
        <div className="flex justify-between sticky top-0 pt-4 pb-2 bg-gray-100 z-10 px-4">
          <div className="justify-start">Recommendations</div>
          <div className="flex justify-end">
            <button
              onClick={() => setAiMessages([])}
              className="bg-gray-300 rounded-full p-1"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-4 h-4"
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
          {chats.map((chat, index) => (
            <div className="mb-4">
              <div key={index} className="flex mb-2">
                <div className="relative bg-gray-300 p-4 rounded-lg shadow-lg w-full">
                  <p className="text-xs mb-4">
                    Responses generated for: <b>low milk production</b>
                  </p>
                  <p className="mb-2">{chat}</p>
                  <div className="flex justify-between items-center border-t border-gray-600 pt-2">
                    <div className="flex justify-start">
                      <button onClick={() => handleCopy(chat)} className="mr-2">
                        {copied ? (
                          <svg
                            id="Layer_1"
                            data-name="Layer 1"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 100.32 122.88"
                            className="w-4 h-4"
                          >
                            <path d="M76.43,113.78a2.89,2.89,0,1,1,5.78,0v3.76a5.32,5.32,0,0,1-1.56,3.76h0a5.27,5.27,0,0,1-3.76,1.57H5.34a5.29,5.29,0,0,1-3.76-1.57h0A5.3,5.3,0,0,1,0,117.54V23.06a5.31,5.31,0,0,1,1.57-3.77l.23-.21a5.29,5.29,0,0,1,3.54-1.35H9A2.89,2.89,0,1,1,9,23.5H5.78v93.6H76.43v-3.32ZM37,85.54a2.65,2.65,0,1,1,0-5.29H62.67a2.65,2.65,0,1,1,0,5.29Zm0-16.21A2.65,2.65,0,0,1,37,64H71.92a2.65,2.65,0,0,1,0,5.3Zm0-16.22a2.65,2.65,0,1,1,0-5.3H82.17a2.65,2.65,0,0,1,0,5.3ZM71,1.05,98.17,29.67a2.9,2.9,0,0,1,2.15,2.8V99.82A5.33,5.33,0,0,1,95,105.15H23.45a5.28,5.28,0,0,1-3.76-1.56h0a5.31,5.31,0,0,1-1.57-3.77V5.34a5.3,5.3,0,0,1,1.57-3.77l.23-.21A5.25,5.25,0,0,1,23.45,0H68.73A2.89,2.89,0,0,1,71,1.05ZM94.54,36H68.73a2.89,2.89,0,0,1-2.89-2.89V5.78H23.89v93.6H94.54V36Zm-3.83-5.78L71.62,10.11V30.19Z" />
                          </svg>
                        ) : (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            shape-rendering="geometricPrecision"
                            text-rendering="geometricPrecision"
                            image-rendering="optimizeQuality"
                            fill-rule="evenodd"
                            clip-rule="evenodd"
                            viewBox="0 0 438 512.37"
                            className="w-4 h-4"
                          >
                            <path
                              fill-rule="nonzero"
                              d="M107.62 54.52V25.03c0-6.9 2.82-13.16 7.34-17.69C119.49 2.82 125.75 0 132.65 0h191.46c3.22 0 6.1 1.45 8.03 3.74l102.87 105.4c1.97 2.03 2.96 4.66 2.96 7.29l.03 316.39c0 6.82-2.82 13.07-7.36 17.62l-.04.05c-4.57 4.54-10.82 7.36-17.63 7.36h-82.59v29.49c0 6.84-2.81 13.09-7.35 17.64l-.04.04c-4.57 4.54-10.8 7.35-17.64 7.35H25.03c-6.9 0-13.16-2.82-17.69-7.34C2.82 500.5 0 494.24 0 487.34V79.56c0-6.91 2.82-13.17 7.34-17.69 4.53-4.53 10.79-7.35 17.69-7.35h82.59zm309.41 76.03h-78.85c-8.54 0-16.31-3.51-21.95-9.14l-.04-.04c-5.64-5.64-9.14-13.41-9.14-21.95V20.97h-174.4c-1.1 0-2.12.46-2.86 1.2-.73.74-1.2 1.76-1.2 2.86v29.49h57.68c3.21 0 6.09 1.45 8.01 3.73l133.07 135.56c2 2.03 3 4.69 3 7.33l.03 235.73h82.59c1.11 0 2.12-.45 2.84-1.17l.04-.04c.72-.72 1.18-1.73 1.18-2.84V130.55zm-11.69-20.97-77.32-78.77v68.61c0 2.8 1.14 5.35 2.97 7.19 1.84 1.83 4.39 2.97 7.19 2.97h67.16zm-95.93 107.27h-106.4c-10.24 0-19.55-4.19-26.29-10.92-6.73-6.73-10.92-16.05-10.92-26.29V75.5H25.03c-1.1 0-2.12.46-2.86 1.2-.73.73-1.2 1.75-1.2 2.86v407.78c0 1.1.47 2.12 1.2 2.86.74.74 1.76 1.2 2.86 1.2h280.32c1.13 0 2.14-.45 2.85-1.16l.05-.05c.71-.71 1.16-1.72 1.16-2.85V216.85zm-12.14-20.97L186.77 83.31v96.33c0 4.45 1.84 8.52 4.78 11.46 2.95 2.95 7.01 4.78 11.46 4.78h94.26z"
                            />
                          </svg>
                        )}
                      </button>
                      <button onClick={() => handleReload(chat)}>
                        <svg
                          version="1.1"
                          id="Layer_1"
                          xmlns="http://www.w3.org/2000/svg"
                          x="0px"
                          y="0px"
                          width="118.307px"
                          height="122.88px"
                          viewBox="0 0 118.307 122.88"
                          className="w-4 h-4"
                        >
                          <g>
                            <path d="M10.03,35.673c2.245-10.496,7.201-19.176,14.246-25.362C32.504,3.086,43.498-0.674,56.271,0.1 c1.916,0.113,3.377,1.758,3.265,3.674c-0.113,1.916-1.757,3.378-3.673,3.265C44.988,6.379,35.71,9.509,28.848,15.535 c-6.483,5.693-10.883,14.028-12.512,24.258l0.639,0.264l10.389-7.172c1.425-0.986,3.38-0.63,4.367,0.795 c0.986,1.426,0.63,3.381-0.795,4.366l-16.557,11.43c-1.425,0.986-3.38,0.63-4.366-0.795c-0.062-0.089-0.118-0.18-0.169-0.272 L9.84,48.409L0.39,31.146c-0.836-1.52-0.282-3.431,1.238-4.267c1.52-0.836,3.43-0.282,4.266,1.238L10.03,35.673L10.03,35.673z M99.032,23.108l-0.206,0.159l1.016,12.583c0.142,1.728-1.145,3.243-2.872,3.384c-1.727,0.142-3.242-1.145-3.384-2.872 L91.967,16.31c-0.142-1.728,1.144-3.243,2.871-3.384c0.108-0.009,0.215-0.013,0.32-0.011l0.001-0.002l19.675,0.446 c1.734,0.036,3.112,1.471,3.076,3.206c-0.035,1.734-1.471,3.111-3.206,3.075l-9.65-0.219c3.769,4.437,6.799,9.422,9.01,14.762 c2.775,6.698,4.243,13.922,4.243,21.281c0,3.63-0.358,7.25-1.064,10.812c-0.7,3.535-1.755,7.021-3.153,10.409 c-0.729,1.773-2.757,2.62-4.53,1.891c-1.773-0.729-2.619-2.757-1.891-4.529c1.207-2.924,2.125-5.974,2.745-9.104 c0.616-3.104,0.928-6.279,0.928-9.478c0-6.476-1.279-12.804-3.698-18.643C105.583,31.85,102.684,27.207,99.032,23.108 L99.032,23.108z M72.658,109.86c-5.729,1.047-11.558,1.181-17.277,0.427c-7.172-0.943-14.162-3.288-20.552-6.978l-0.01-0.006 l-0.003,0.006c-3.14-1.813-6.097-3.934-8.832-6.328c-2.73-2.392-5.223-5.045-7.437-7.923c-1.172-1.519-0.892-3.699,0.625-4.871 s3.699-0.892,4.871,0.626c1.948,2.533,4.131,4.857,6.512,6.943c2.377,2.082,4.97,3.939,7.743,5.54l-0.003,0.006 c5.588,3.225,11.705,5.274,17.983,6.101c5.35,0.705,10.824,0.517,16.196-0.593l-0.035-0.264l-11.405-5.411 c-1.566-0.741-2.236-2.612-1.495-4.179c0.741-1.567,2.613-2.236,4.18-1.495l18.177,8.624c1.566,0.741,2.235,2.612,1.494,4.18 c-0.046,0.097-0.097,0.191-0.15,0.282l0.002,0.001l-10.225,16.816c-0.898,1.483-2.83,1.959-4.314,1.061 c-1.484-0.897-1.96-2.829-1.062-4.313L72.658,109.86L72.658,109.86z" />
                          </g>
                        </svg>
                      </button>
                    </div>
                    <div className="text-right text-xs justify-end">
                      AI - {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const ChatWindow = () => {
  const chatContext = useChatContext();
  const chatDispatch = useChatDispatch();

  const { clientName, clientPhoneNumber } = chatContext;

  const textareaRef = useRef(null);
  const [message, setMessage] = useState("");
  const [aiMessages, setAiMessages] = useState([]);
  const [chats, setChats] = useState([]);

  useEffect(() => {
    function onChats(value) {
      console.info(value, "socket chats");
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
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis eget sollicitudin augue.",
        "Curabitur quis risus ut nulla consectetur gravida. Nunc sit amet turpis tempor, rutrum mi vel, molestie purus.",
      ]);
    }, 2000);
  }, []);

  useLayoutEffect(() => {
    // Trigger on chats change to scroll to the bottom
    const messagesContainer = document.getElementById("messagesContainer");
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
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
      setChats((previous) => [...previous, chatPayload]);
      socket.timeout(5000).emit("chats", chatPayload);
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
          <ChatMessages chats={chats} />
        </div>

        {/* AI Messages */}
        {aiMessages.length ? <AiMessages chats={aiMessages} /> : ""}
      </div>

      {/* TextArea */}
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
