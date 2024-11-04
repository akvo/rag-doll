"use client";

import React, {
  useState,
  useMemo,
  useCallback,
  useRef,
  useEffect,
} from "react";
import { formatChatTime } from "@/utils/formatter";
import { useChatContext } from "@/context/ChatContextProvider";
import MarkdownRenderer from "./MarkdownRenderer";
import { CopiedIcon, ExpandIcon, CopyIcon } from "@/utils/icons";
import Image from "next/image";
import { SenderRoleEnum } from "./ChatWindow";

const Whisper = ({
  whisperChats,
  textareaRef,
  handleTextAreaDynamicHeight,
  setMessage,
  setUseWhisperAsTemplate,
  clients,
  lastChatHistory,
  maxHeight,
  setMaxHeight,
  scrollToLastMessage,
}) => {
  const whisperMessageRef = useRef(null);
  const chatContext = useChatContext();
  const { clientPhoneNumber } = chatContext;

  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [whisperHeight, setWhisperHeight] = useState(0);

  useEffect(() => {
    if (expanded) {
      scrollToLastMessage(maxHeight / 2);
    }
  }, [expanded, scrollToLastMessage, maxHeight]);

  // handle whisper deduplication here
  const whispers = useMemo(() => {
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
    return filterWhisper;
  }, [whisperChats, clientPhoneNumber, clients, lastChatHistory]);

  const currentWhisper = useMemo(
    () => whispers.find((c) => c.clientPhoneNumber === clientPhoneNumber),
    [whispers, clientPhoneNumber]
  );

  const handleCopy = useCallback(
    async ({ message }) => {
      try {
        await navigator.clipboard.writeText(message);
        if (textareaRef.current) {
          textareaRef.current.value = message;
          setMessage(message);
          handleTextAreaDynamicHeight();
        }
        setCopied(true);
        setUseWhisperAsTemplate(true);
        setTimeout(() => setCopied(false), 1000);
      } catch (error) {
        console.error("Failed to copy text: ", error);
      }
    },
    [
      textareaRef,
      setMessage,
      handleTextAreaDynamicHeight,
      setUseWhisperAsTemplate,
    ]
  );

  const toggleExpand = useCallback(() => {
    setExpanded((prev) => !prev);
  }, []);

  useEffect(() => {
    if (!expanded) {
      setMaxHeight(0);
      return;
    }
    const calculateMaxHeight = () => {
      // Calculate 2/3 of the viewport height
      const calculatedMaxHeight = (window.innerHeight * 2) / 3;
      setMaxHeight(calculatedMaxHeight);
    };

    const handleResize = () => {
      calculateMaxHeight();
    };

    // Initial calculation
    calculateMaxHeight();

    // Update max height on window resize
    window.addEventListener("resize", handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [expanded, setMaxHeight]);

  useEffect(() => {
    if (whisperMessageRef.current) {
      setWhisperHeight(whisperMessageRef.current.clientHeight + 85);
    }
  }, [whispers, expanded]);

  if (!currentWhisper && whispers.length === 0) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-16 w-full flex mt-12 px-4 pt-4 pb-6 overflow-auto bg-gray-100`}
      style={{
        height: expanded ? Math.min(whisperHeight, maxHeight) : "11.625rem",
      }}
    >
      <div
        className={`w-full relative bg-white border-white border-2 border-solid rounded-lg shadow-inner overflow-auto`}
        style={{
          maxHeight: expanded ? `${maxHeight}px` : "11.625rem",
        }}
      >
        <div className="flex justify-between sticky top-0 pt-4 pb-2 bg-white z-10 px-4">
          <div className="flex items-center">
            <div>
              <Image
                src="/images/whisper-logo.png"
                alt="whisper-logo"
                className="h-4 w-4"
                width={4}
                height={4}
              />
            </div>
            <div className="ml-2 text-sm font-semibold">
              Suggested Resources
            </div>
          </div>
          <div className="flex">
            <button
              onClick={toggleExpand}
              className={`w-5 h-5 bg-gray-100 rounded-full p-1 ${
                expanded ? "rotate-180" : ""
              }`}
              disabled={currentWhisper?.loading}
            >
              <ExpandIcon />
            </button>
          </div>
        </div>
        <div className="p-4" ref={whisperMessageRef}>
          {/* AI Loading */}
          {currentWhisper?.loading ? (
            <div className="flex h-10 items-center justify-center">
              <div className="flex items-center space-x-2">
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="w-1 h-1 bg-green-500 rounded-full animate-bounce delay-150"></div>
                <div className="w-1 h-1 bg-red-500 rounded-full animate-bounce delay-300"></div>
              </div>
              <p className="ml-4 text-sm font-medium text-gray-600">
                Loading suggested response
              </p>
            </div>
          ) : (
            whispers.map((chat, index) => (
              <div key={index} className="mb-4">
                <div className="flex mb-2">
                  <div className="w-full">
                    {chat?.message?.split("\n")?.map((line, index) => (
                      <MarkdownRenderer
                        key={`ai-${index}`}
                        content={line}
                        className="text-sm"
                      />
                    ))}
                    <div className="border-t border-gray-600 my-2"></div>
                    <div className="flex justify-between items-center ">
                      <div className="flex justify-start">
                        <button
                          onClick={() => handleCopy(chat)}
                          className="mr-2 flex justify-start"
                        >
                          {/* Copy */}
                          {copied ? (
                            <div className="flex items-center">
                              <CopiedIcon />
                              <p className="text-xs font-medium ms-2 text-akvo-green">
                                Copied!
                              </p>
                            </div>
                          ) : (
                            <div className="flex items-center">
                              <CopyIcon />
                              <p className="text-xs font-medium ms-2 text-gray-500">
                                Use this message
                              </p>
                            </div>
                          )}
                        </button>
                      </div>
                      <p className="text-xs text-gray-500">
                        {formatChatTime(chat.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Whisper;
