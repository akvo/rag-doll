"use client";

import {
  useRef,
  useState,
  useEffect,
  useCallback,
  useMemo,
  forwardRef,
} from "react";
import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserDispatch } from "@/context/UserContextProvider";
import { socket, api, dbLib } from "@/lib";
import {
  formatChatTime,
  generateMessage,
  check24hrWindow,
} from "@/utils/formatter";
import { v4 as uuidv4 } from "uuid";
import Whisper from "./Whisper";
import MarkdownRenderer from "./MarkdownRenderer";
import { BackIcon, SendIcon, ThreeDotIcon } from "@/utils/icons";
import Image from "next/image";
import ChatMedia from "./ChatMedia";
import { deleteCookie } from "@/lib/cookies";
import { useRouter } from "next/navigation";
import Loading from "@/app/loading";
import FarmerForm from "./FarmerForm";
import Notification from "../utils/Notification";

export const SenderRoleEnum = {
  USER: "user",
  CLIENT: "client",
  ASSISTANT: "assistant",
  SYSTEM: "system",
  USER_BROADCAST: "user_broadcast",
};

export const ChatStatusEnum = {
  UNREAD: "UNREAD",
  READ: "READ",
};

const ChatIDPrefix = "CHAT-";

const UserChat = forwardRef(({ message, timestamp, refTemp }, ref) => {
  return (
    <div className="flex mb-4 justify-end" ref={refTemp}>
      <div className="relative bg-akvo-green-100 p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
        <div className="absolute bottom-0 right-0 w-0 h-0 border-t-8 border-t-akvo-green-100 border-r-8 border-r-transparent border-b-0 border-l-8 border-l-transparent transform -translate-x-1/2 translate-y-1/2"></div>
        {message?.split("\n")?.map((line, i) => (
          <MarkdownRenderer
            key={`user-${i}`}
            content={line}
            className={`prose-headings:text-gray-800 prose-strong:text-gray-800 prose-p:text-gray-800 prose-a:text-gray-800 prose-li:text-gray-800 prose-ol:text-gray-800 prose-ul:text-gray-800 prose-code:text-gray-800 text-gray-800`}
          />
        ))}
        <p className="text-right text-xs mt-2 text-gray-800">
          {formatChatTime(timestamp)}
        </p>
      </div>
    </div>
  );
});
UserChat.displayName = "UserChat";

const ClientChat = forwardRef(
  ({ message, timestamp, media = [], refTemp, id }, ref) => {
    return (
      <div className="flex mb-4" ref={refTemp} id={id}>
        <div className="relative bg-gray-300 p-4 rounded-lg shadow-lg max-w-xs md:max-w-md font-medium">
          <div className="absolute bottom-0 left-0 w-0 h-0 border-t-8 border-t-gray-300 border-l-8 border-l-transparent border-b-0 border-r-8 border-r-transparent transform translate-x-1/2 translate-y-1/2"></div>
          {media.map((item, i) => (
            <ChatMedia key={`media-${i}`} type={item.type} url={item.url} />
          ))}
          {message?.split("\n")?.map((line, i) => (
            <MarkdownRenderer key={`client-${i}`} content={line} />
          ))}
          <p className="text-right text-xs mt-2">{formatChatTime(timestamp)}</p>
        </div>
      </div>
    );
  }
);
ClientChat.displayName = "ClientChat";

const SystemChat = forwardRef(({ message, timestamp, refTemp }, ref) => (
  <div className="flex mb-4 justify-center" ref={refTemp}>
    <div className="relative bg-blue-100 p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
      {message?.split("\n")?.map((line, i) => (
        <MarkdownRenderer
          key={`system-${i}`}
          content={line}
          className={`prose-headings:text-gray-800 prose-strong:text-gray-800 prose-p:text-gray-800 prose-a:text-gray-800 prose-li:text-gray-800 prose-ol:text-gray-800 prose-ul:text-gray-800 prose-code:text-gray-800 text-gray-800`}
        />
      ))}
      <p className="text-right text-xs mt-2 text-gray-800">
        Automatic system message - {formatChatTime(timestamp)}
      </p>
    </div>
  </div>
));
SystemChat.displayName = "SystemChat";

const BroadcastChat = forwardRef(({ message, timestamp, refTemp }, ref) => (
  <div className="flex mb-4 justify-center" ref={refTemp}>
    <div className="relative bg-orange-100 p-4 rounded-lg shadow-lg max-w-xs md:max-w-md">
      {message?.split("\n")?.map((line, i) => (
        <MarkdownRenderer
          key={`system-${i}`}
          content={line}
          className={`prose-headings:text-gray-800 prose-strong:text-gray-800 prose-p:text-gray-800 prose-a:text-gray-800 prose-li:text-gray-800 prose-ol:text-gray-800 prose-ul:text-gray-800 prose-code:text-gray-800 text-gray-800`}
        />
      ))}
      <p className="text-right text-xs mt-2 text-gray-800">
        {formatChatTime(timestamp)}
      </p>
    </div>
  </div>
));
BroadcastChat.displayName = "BroadcastChat";

const ChatWindow = ({
  chats,
  setChats,
  whisperChats,
  setWhisperChats,
  useWhisperAsTemplate,
  setUseWhisperAsTemplate,
  setClients,
  clients,
}) => {
  const chatContext = useChatContext();
  const chatDispatch = useChatDispatch();
  const authDispatch = useAuthDispatch();
  const userDispatch = useUserDispatch();
  const router = useRouter();

  const { clientId, clientName, clientPhoneNumber } = chatContext;

  const textareaRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const lastMessageRef = useRef(null);
  const dropdownRef = useRef(null);

  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [maxHeight, setMaxHeight] = useState(0);

  const [showNotification, setShowNotification] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");
  const [conversationTimeout, setConversationTimeout] = useState({
    sendConversationReconnectTemplate: false,
    disableMessageInput: false,
  });

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNotificationContent("");
    }, 3000);
  };

  const copyToClipboard = (url) => {
    url = `${location.origin}${url}`;
    navigator.clipboard
      .writeText(url)
      .then(() => {
        setNotificationContent("Data Retention Policy URL copied.");
        handleShowNotification();
      })
      .catch((error) => {
        console.error("Failed to copy: ", error);
      });
  };

  const firstUnreadMessage = useMemo(() => {
    return chatHistory.find((ch) => ch.status === ChatStatusEnum.UNREAD);
  }, [chatHistory]);

  const scrollToLastMessage = useCallback((currentHeight = 0) => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight + currentHeight;
    }
  }, []);

  // handle onRead message for chat history and incoming chat
  useEffect(() => {
    if (firstUnreadMessage?.chat_session_id && socket.connected) {
      socket.emit("read_message", firstUnreadMessage.chat_session_id);
    }
    if (chats.length && socket.connected) {
      let chat_session_id = null;
      const findChat = chats.find(
        (c) => c.conversation_envelope.client_phone_number === clientPhoneNumber
      );
      if (findChat?.conversation_envelope?.chat_session_id) {
        chat_session_id = findChat.conversation_envelope.chat_session_id;
      }
      socket.emit("read_message", chat_session_id);
    }
  }, [firstUnreadMessage, chats, clientPhoneNumber]);

  // Scroll to the last message whenever chats or chatHistory state changes
  useEffect(() => {
    const scrollToLastMessageWithDelay = () => {
      setTimeout(() => {
        if (
          !firstUnreadMessage &&
          (chats?.length > 0 || chatHistory?.length > 0)
        ) {
          scrollToLastMessage();
        }
        if (firstUnreadMessage) {
          const id = `${ChatIDPrefix}${firstUnreadMessage.id}`;
          const lastChat = document.getElementById(id);
          lastChat?.scrollIntoView({ behavior: "smooth" });
        }
      }, 500);
    };
    scrollToLastMessageWithDelay();
  }, [chats, chatHistory, scrollToLastMessage, firstUnreadMessage, isEdit]);

  // Intersection observer setup to scroll when new message arrives
  useEffect(() => {
    const lastMessageRefTemp = lastMessageRef.current;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          scrollToLastMessage();
        }
      },
      { threshold: 0.5 }
    );

    if (lastMessageRefTemp) {
      observer.observe(lastMessageRefTemp);
    }

    return () => {
      if (lastMessageRefTemp) {
        observer.unobserve(lastMessageRefTemp);
      }
    };
  }, [lastMessageRef, scrollToLastMessage]);

  // Load previous chats from /api/chat-details/{clientId}
  useEffect(() => {
    async function fetchChats() {
      try {
        setLoading(true);
        const res = await api.get(`/chat-details/${clientId}`);
        if (res.status === 200) {
          const data = await res.json();
          setChatHistory(data.messages);
          setClients((prev) =>
            prev.map((p) => {
              if (p.client_id === clientId) {
                return {
                  ...p,
                  message_ids: data.messages.map((d) => d.id),
                };
              }
              return p;
            })
          );
        }
        if (res.status === 401 || res.status === 403) {
          userDispatch({
            type: "DELETE",
          });
          authDispatch({ type: "DELETE" });
          deleteCookie("AUTH_TOKEN");
          setLoading(false);
          router.replace("/login");
        } else {
          setLoading(false);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchChats();
  }, [
    clientId,
    scrollToLastMessage,
    authDispatch,
    router,
    userDispatch,
    setClients,
  ]);

  // handle check the conversation timeout
  useEffect(() => {
    const getLastMessage = async () => {
      const res = await dbLib.lastMessageTimestamp.getByClientPhoneNumber(
        clientPhoneNumber
      );
      if (res) {
        const { user_message_timestamp, client_message_timestamp } = res;
        const isClientMessageBeyond24hr = check24hrWindow(
          client_message_timestamp
        );
        setConversationTimeout({
          // If no message has yet been sent after 24 hours then on load the UI should communicate that you can only send one message
          sendConversationReconnectTemplate:
            isClientMessageBeyond24hr && !user_message_timestamp,
          // Disable the input if > 24 hours since last farmer(client) message AND there is one message sent (user) after 24 hours.
          disableMessageInput:
            isClientMessageBeyond24hr && user_message_timestamp,
        });
      }
    };
    getLastMessage();
  }, [chats, clientPhoneNumber]);
  // TODO :: use this state to show notification and disable input
  console.log(conversationTimeout);

  const lastChatHistory = useMemo(() => {
    if (chatHistory?.length) {
      return chatHistory.slice(-1)[0];
    }
    return null;
  }, [chatHistory]);

  const handleTextAreaDynamicHeight = () => {
    const textarea = textareaRef.current;
    const maxHeight = 250;
    textarea.style.height = "auto"; // Reset height to auto
    textarea.style.height =
      textarea.scrollHeight <= maxHeight
        ? `${textarea.scrollHeight}px`
        : `${maxHeight}px`; // Set height based on scroll height
  };

  const handleChange = (event) => {
    setUseWhisperAsTemplate(false);
    setMessage(event.target.value);
  };

  const handleOnClickBack = () => {
    if (isEdit) {
      setIsEdit(false);
    } else {
      chatDispatch({
        type: "CLEAR",
      });
    }
  };

  // Close the dropdown if clicked outside
  const handleClickOutside = (event) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
      setDropdownOpen(false);
    }
  };

  useEffect(() => {
    // Add event listener to detect clicks outside
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      // Cleanup the event listener on component unmount
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleLostMessage = async (chatPayload) => {
    const res = await dbLib.messages.add({
      chat_session_id: chatPayload.conversation_envelope.chat_session_id,
      message: chatPayload,
      sender_role: chatPayload.conversation_envelope.sender_role,
      created_at: chatPayload.conversation_envelope.timestamp,
    });
    return res;
  };

  const handleSend = async () => {
    if (message.trim()) {
      let chatBreakdown = {};
      const lastChat = chats.slice(-1)[0];
      if (lastChat && lastChat?.conversation_envelope) {
        chatBreakdown = {
          ...lastChat,
          ...lastChat.conversation_envelope,
          message_id: uuidv4(),
        };
      } else {
        chatBreakdown = {
          platform: "WHATSAPP",
          message_id: uuidv4(),
        };
      }
      const chatPayload = generateMessage({
        ...chatBreakdown,
        client_phone_number: clientPhoneNumber,
        sender_role: SenderRoleEnum.USER,
        body: message,
        transformation_log: null,
        chat_session_id: lastChatHistory?.chat_session_id || null,
        timestamp: null,
      });
      setChats((previous) => [...previous, chatPayload]);
      setMessage(""); // Clear the textarea after sending
      textareaRef.current.style.height = "auto"; // Reset the height after sending
      try {
        if (socket.connected) {
          const response = await socket
            .timeout(5000)
            .emitWithAck("chats", chatPayload);
          console.info(`Success send message: ${JSON.stringify(response)}`);
          if (useWhisperAsTemplate) {
            // remove whisper
            setWhisperChats((prev) =>
              prev.filter((p) => p.clientPhoneNumber !== clientPhoneNumber)
            );
            setMaxHeight(0);
          }
        } else {
          handleLostMessage(chatPayload);
          console.info(`Socket status: ${socket.connected}`);
        }
        // add or update lastMessage
        await dbLib.lastMessageTimestamp.addOrUpdate({
          chat_session_id: chatPayload.conversation_envelope.chat_session_id,
          client_phone_number:
            chatPayload.conversation_envelope.client_phone_number,
          sender_role: chatPayload.conversation_envelope.sender_role,
          created_at: chatPayload.conversation_envelope.timestamp,
        });
      } catch (err) {
        handleLostMessage(chatPayload);
        console.error(`Failed send message: ${JSON.stringify(err)}`);
      }
    }
  };

  const renderChatHistory = useMemo(() => {
    return chatHistory?.map((c, ci) => {
      if (c.sender_role === SenderRoleEnum.USER) {
        return (
          <UserChat
            key={`user-history-${ci}`}
            message={c.message}
            timestamp={c.created_at}
          />
        );
      }
      if (c.sender_role === SenderRoleEnum.SYSTEM) {
        return (
          <SystemChat
            key={`system-history-${ci}`}
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
            media={c.media}
            timestamp={c.created_at}
            id={`${ChatIDPrefix}${c.id}`}
          />
        );
      }
      if (c.sender_role === SenderRoleEnum.USER_BROADCAST) {
        return (
          <BroadcastChat
            key={`user-broadcast-history-${ci}`}
            message={c.message}
            timestamp={c.created_at}
          />
        );
      }
    });
  }, [chatHistory]);

  const renderChats = useMemo(() => {
    // Handle duplicated message from reconnected event with chat history
    const clientChats = chats.filter((chat) => {
      const isChatInHistory = chatHistory.find(
        (ch) => ch.id === chat.conversation_envelope.message_id
      )
        ? true
        : false;
      return (
        chat.conversation_envelope.client_phone_number === clientPhoneNumber &&
        !isChatInHistory
      );
    });
    return clientChats.map((c, ci) => {
      if (c?.conversation_envelope?.sender_role === SenderRoleEnum.USER) {
        return (
          <UserChat
            key={`user-${ci}`}
            message={c.body}
            timestamp={c.conversation_envelope.timestamp}
            refTemp={ci === chats.length - 1 ? lastMessageRef : null}
          />
        );
      }
      if (c?.conversation_envelope?.sender_role === SenderRoleEnum.SYSTEM) {
        return (
          <SystemChat
            key={`user-${ci}`}
            message={c.body}
            timestamp={c.conversation_envelope.timestamp}
            refTemp={ci === chats.length - 1 ? lastMessageRef : null}
          />
        );
      }
      if (c?.conversation_envelope?.sender_role === SenderRoleEnum.CLIENT) {
        return (
          <ClientChat
            key={`client-${ci}`}
            message={c.body}
            media={c.media}
            timestamp={c.conversation_envelope.timestamp}
            refTemp={ci === chats.length - 1 ? lastMessageRef : null}
          />
        );
      }
    });
  }, [chats, clientPhoneNumber, chatHistory]);

  const isWhisperVisible = useMemo(() => {
    const isWhisperInLastChatHistory =
      lastChatHistory?.sender_role === SenderRoleEnum.ASSISTANT;
    const findClient = clients.find(
      (c) => c.phone_number === clientPhoneNumber
    );
    // handle whisper deduplication
    const filterWhisper = whisperChats.filter((wc) => {
      const isMessageInMessageIds = findClient?.message_ids?.length
        ? findClient.message_ids.find((id) => id === wc.message_id) &&
          !isWhisperInLastChatHistory
        : false;
      return (
        wc.clientPhoneNumber === clientPhoneNumber && !isMessageInMessageIds
      );
    });
    return filterWhisper.length > 0;
  }, [whisperChats, clientPhoneNumber, clients, lastChatHistory]);

  return (
    <div className="relative flex flex-col w-full bg-gray-100">
      {/* Chat Header */}
      <div className="flex items-center p-4 bg-white border-b h-18 fixed top-0 left-0 right-0 z-10">
        <button className="mr-4 flex-start" onClick={handleOnClickBack}>
          <BackIcon />
        </button>

        <Image
          src="/images/bg-login-page.png"
          alt="User Avatar"
          className="rounded-full mr-4 w-12 h-12 bg-gray-300"
          width={12}
          height={12}
        />

        <div className="flex-1">
          <h3 className="text-md font-semibold">
            {clientName || clientPhoneNumber}
          </h3>
          <p className="text-xs text-gray-500">Online</p>
        </div>

        <button
          className="flex-end"
          onClick={() => setDropdownOpen((prev) => !prev)}
        >
          <ThreeDotIcon />
        </button>
        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div
            ref={dropdownRef}
            className="absolute right-0 mt-24 mr-4 w-48 bg-white border rounded shadow-lg z-20"
          >
            <ul className="py-1">
              <li
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                onClick={() => {
                  setIsEdit((prev) => !prev);
                  setDropdownOpen(false);
                }}
              >
                Edit Farmer Detail
              </li>
              <li
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                onClick={() => {
                  setDropdownOpen(false);
                  copyToClipboard("/data-retention-policy");
                }}
              >
                Data Retention Policy
              </li>
            </ul>
          </div>
        )}
      </div>

      {isEdit ? (
        <FarmerForm
          isEdit={isEdit}
          clientId={clientId}
          clientName={clientName || clientPhoneNumber}
          clientPhoneNumber={clientPhoneNumber}
          chatDispatch={chatDispatch}
        />
      ) : (
        <div>
          {/* Chat Messages */}
          <div
            className={`flex flex-col flex-grow pt-20 w-full h-full ${
              isWhisperVisible ? "pb-40" : "pb-0"
            }`}
            style={{
              maxHeight: `calc(100vh - ${maxHeight ? maxHeight / 2 : 80}px)`,
            }} // Adjust for header and textarea
          >
            {loading ? (
              <Loading />
            ) : (
              <>
                {/* User Messages */}
                <div
                  ref={messagesContainerRef}
                  className="flex-1 p-4 overflow-auto"
                >
                  {renderChatHistory}
                  {renderChats}
                </div>
                {/* AI Messages */}
                <Whisper
                  whisperChats={whisperChats}
                  setWhisperChats={setWhisperChats}
                  textareaRef={textareaRef}
                  handleTextAreaDynamicHeight={handleTextAreaDynamicHeight}
                  setMessage={setMessage}
                  setUseWhisperAsTemplate={setUseWhisperAsTemplate}
                  clients={clients}
                  lastChatHistory={lastChatHistory}
                  maxHeight={maxHeight}
                  setMaxHeight={setMaxHeight}
                  scrollToLastMessage={scrollToLastMessage}
                />
              </>
            )}
          </div>

          {/* TextArea */}
          <div className="flex p-4 bg-white border-t items-center fixed bottom-0 w-full z-20">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleChange}
              onInput={handleTextAreaDynamicHeight}
              placeholder="Type a message..."
              className="w-full px-4 py-2 border rounded-lg resize-none overflow-auto tex-md"
              rows={1}
            />
            <button
              onClick={handleSend}
              className="ml-4 bg-akvo-green hover:bg-green-700 text-white p-3 rounded-full focus:outline-none"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      )}

      <Notification message={notificationContent} show={showNotification} />
    </div>
  );
};

export default ChatWindow;
