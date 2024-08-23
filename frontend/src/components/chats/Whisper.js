"use client";

import React, { useState, useMemo } from "react";
import { formatChatTime } from "@/utils/formatter";
import { useChatContext } from "@/context/ChatContextProvider";
import MarkdownRenderer from "./MarkdownRenderer";

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
    [whisperChats, clientPhoneNumber],
  );

  const whispers = useMemo(
    () =>
      whisperChats.filter(
        (chat) => chat.clientPhoneNumber === clientPhoneNumber,
      ),
    [whisperChats, clientPhoneNumber],
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
      prev.filter((p) => p.clientPhoneNumber !== clientPhoneNumber),
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
        className={`w-full relative h- bg-blue-300 border-blue-300 border-2 border-solid rounded-lg shadow-inner overflow-auto min-h-40 ${
          expanded ? "max-h-3/4" : "h-40"
        }`}
      >
        <div className="flex justify-between sticky top-0 pt-4 pb-2 bg-blue-300 z-10 px-4">
          <div className="justify-start">Recommendations</div>
          <div className="flex space-x-2">
            <button
              onClick={toggleExpand}
              className="bg-gray-100 rounded-full p-1"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className={`w-4 h-4 ${expanded ? "rotate-180" : ""}`}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 15l-7.5-7.5L4.5 15"
                />
              </svg>
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
            <div className="flex h-18 items-center justify-center">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce delay-150"></div>
                <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce delay-300"></div>
              </div>
              <p className="ml-4 text-lg font-medium text-gray-600">
                AI is thinking...
              </p>
            </div>
          ) : (
            whispers.map((chat, index) => (
              <div key={index} className="mb-4">
                <div className="flex mb-2">
                  <div className="relative bg-gray-100 p-4 rounded-lg shadow-lg w-full">
                    {chat.message.split("\n")?.map((line, index) => (
                      <MarkdownRenderer key={`ai-${index}`} content={line} />
                    ))}
                    <div className="flex justify-between items-center border-t border-gray-600 pt-2">
                      <div className="flex justify-start">
                        <button
                          onClick={() => handleCopy(chat)}
                          className="mr-2 flex justify-start"
                        >
                          {/* Copy */}
                          {copied ? (
                            <svg
                              id="Layer_1"
                              xmlns="http://www.w3.org/2000/svg"
                              viewBox="0 0 100.32 122.88"
                              className="w-4 h-4"
                            >
                              <path d="M76.43,113.78a2.89,2.89,0,1,1,5.78,0v3.76a5.32,5.32,0,0,1-1.56,3.76h0a5.27,5.27,0,0,1-3.76,1.57H5.34a5.29,5.29,0,0,1-3.76-1.57h0A5.3,5.3,0,0,1,0,117.54V23.06a5.31,5.31,0,0,1,1.57-3.77l.23-.21a5.29,5.29,0,0,1,3.54-1.35H9A2.89,2.89,0,1,1,9,23.5H5.78v93.6H76.43v-3.32ZM37,85.54a2.65,2.65,0,1,1,0-5.29H62.67a2.65,2.65,0,1,1,0,5.29Zm0-16.21A2.65,2.65,0,0,1,37,64H71.92a2.65,2.65,0,0,1,0,5.3Zm0-16.22a2.65,2.65,0,1,1,0-5.3H82.17a2.65,2.65,0,0,1,0,5.3ZM71,1.05,98.17,29.67a2.9,2.9,0,0,1,2.15,2.8V99.82A5.33,5.33,0,0,1,95,105.15H23.45a5.28,5.28,0,0,1-3.76-1.56h0a5.31,5.31,0,0,1-1.57-3.77V5.34a5.3,5.3,0,0,1,1.57-3.77l.23-.21A5.25,5.25,0,0,1,23.45,0H68.73A2.89,2.89,0,0,1,71,1.05ZM94.54,36H68.73a2.89,2.89,0,0,1-2.89-2.89V5.78H23.89v93.6H94.54V36Zm-3.83-5.78L71.62,10.11V30.19Z" />
                            </svg>
                          ) : (
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              shapeRendering="geometricPrecision"
                              textRendering="geometricPrecision"
                              imageRendering="optimizeQuality"
                              fillRule="evenodd"
                              clipRule="evenodd"
                              viewBox="0 0 438 512.37"
                              className="w-4 h-4"
                            >
                              <path
                                fillRule="nonzero"
                                d="M107.62 54.52V25.03c0-6.9 2.82-13.16 7.34-17.69C119.49 2.82 125.75 0 132.65 0h191.46c3.22 0 6.1 1.45 8.03 3.74l102.87 105.4c1.97 2.03 2.96 4.66 2.96 7.29l.03 316.39c0 6.82-2.82 13.07-7.36 17.62l-.04.05c-4.57 4.54-10.82 7.36-17.63 7.36h-82.59v29.49c0 6.84-2.81 13.09-7.35 17.64l-.04.04c-4.57 4.54-10.8 7.35-17.64 7.35H25.03c-6.9 0-13.16-2.82-17.69-7.34C2.82 500.5 0 494.24 0 487.34V79.56c0-6.91 2.82-13.17 7.34-17.69 4.53-4.53 10.79-7.35 17.69-7.35h82.59zm309.41 76.03h-78.85c-8.54 0-16.31-3.51-21.95-9.14l-.04-.04c-5.64-5.64-9.14-13.41-9.14-21.95V20.97h-174.4c-1.1 0-2.12.46-2.86 1.2-.73.74-1.2 1.76-1.2 2.86v29.49h57.68c3.21 0 6.09 1.45 8.01 3.73l133.07 135.56c2 2.03 3 4.69 3 7.33l.03 235.73h82.59c1.11 0 2.12-.45 2.84-1.17l.04-.04c.72-.72 1.18-1.73 1.18-2.84V130.55zm-11.69-20.97-77.32-78.77v68.61c0 2.8 1.14 5.35 2.97 7.19 1.84 1.83 4.39 2.97 7.19 2.97h67.16zm-95.93 107.27h-106.4c-10.24 0-19.55-4.19-26.29-10.92-6.73-6.73-10.92-16.05-10.92-26.29V75.5H25.03c-1.1 0-2.12.46-2.86 1.2-.73.73-1.2 1.75-1.2 2.86v407.78c0 1.1.47 2.12 1.2 2.86.74.74 1.76 1.2 2.86 1.2h280.32c1.13 0 2.14-.45 2.85-1.16l.05-.05c.71-.71 1.16-1.72 1.16-2.85V216.85zm-12.14-20.97L186.77 83.31v96.33c0 4.45 1.84 8.52 4.78 11.46 2.95 2.95 7.01 4.78 11.46 4.78h94.26z"
                              />
                            </svg>
                          )}
                          <p
                            className={`text-xs font-medium ms-3 ${
                              copied ? "text-green-600" : "text-gray-500"
                            }`}
                          >
                            {copied ? "Copied!" : "Use this message"}
                          </p>
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
