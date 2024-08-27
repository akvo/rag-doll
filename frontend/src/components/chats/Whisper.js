"use client";

import React, { useState, useMemo } from "react";
import { formatChatTime } from "@/utils/formatter";
import { useChatContext } from "@/context/ChatContextProvider";
import MarkdownRenderer from "./MarkdownRenderer";
import { Copied, ExpandIcon, Copy } from "@/utils/icons";

const Whisper = ({
  whisperChats,
  setWhisperChats,
  textareaRef,
  handleTextAreaDynamicHeight,
  setMessage,
}) => {
  const chatContext = useChatContext();
  const { clientPhoneNumber } = chatContext;

  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const currentWhisper = useMemo(
    () => whisperChats.find((c) => c.clientPhoneNumber === clientPhoneNumber),
    [whisperChats, clientPhoneNumber]
  );

  const whispers = useMemo(
    () =>
      whisperChats.filter(
        (chat) => chat.clientPhoneNumber === clientPhoneNumber
      ),
    [whisperChats, clientPhoneNumber]
  );

  const handleCopy = async ({ message }) => {
    try {
      await navigator.clipboard.writeText(message);
      if (textareaRef.current) {
        textareaRef.current.value = message;
        setMessage(message);
        handleTextAreaDynamicHeight();
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1000);
    } catch (error) {
      console.error("Failed to copy text: ", error);
    }
  };

  const onClose = () => {
    setWhisperChats((prev) =>
      prev.filter((p) => p.clientPhoneNumber !== clientPhoneNumber)
    );
  };

  const toggleExpand = () => {
    setExpanded(!expanded);
  };

  if (!currentWhisper && whispers.length === 0) {
    return null;
  }

  return (
    <div className="flex p-4 overflow-auto">
      <div
        className={`w-full relative h- bg-white border-white border-2 border-solid rounded-lg shadow-inner overflow-auto min-h-36 ${
          expanded ? "max-h-3/4" : "h-36"
        }`}
      >
        <div className="flex justify-between sticky top-0 pt-4 pb-2 bg-white z-10 px-4">
          <div className="flex items-center">
            <div>
              <img
                src="/images/whisper-logo.png"
                alt="whisper-logo"
                className="h-4 w-4"
              />
            </div>
            <div className="ml-2 text-sm font-semibold">Sugested Resources</div>
          </div>
          <div className="flex">
            <button
              onClick={toggleExpand}
              className={`w-5 h-5 bg-gray-100 rounded-full p-1 ${
                expanded ? "rotate-180" : ""
              }`}
            >
              <ExpandIcon />
            </button>
            {/* <button onClick={onClose} className="bg-gray-100 rounded-full p-1">
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
            </button> */}
          </div>
        </div>
        <div className="p-4">
          {/* AI Loading */}
          {currentWhisper?.loading ? (
            <div className="flex h-10 items-center justify-center">
              <div className="flex items-center space-x-2">
                <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="w-1 h-1 bg-green-500 rounded-full animate-bounce delay-150"></div>
                <div className="w-1 h-1 bg-red-500 rounded-full animate-bounce delay-300"></div>
              </div>
              <p className="ml-4 text-sm font-medium text-gray-600">
                AI is thinking
              </p>
            </div>
          ) : (
            whispers.map((chat, index) => (
              <div key={index} className="mb-4">
                <div className="flex mb-2">
                  <div className="w-full">
                    {chat.message.split("\n")?.map((line, index) => (
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
                              <Copied />
                              <p className="text-xs font-medium ms-2 text-akvo-green">
                                Copied!
                              </p>
                            </div>
                          ) : (
                            <div className="flex items-center">
                              <Copy />
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
