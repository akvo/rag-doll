import React from "react";

const ChatHeader = ({ leftButton }) => {
  return (
    <div className="sticky top-0 left-0 right-0 bg-gray-100 z-10 px-2 border-b border-gray-100">
      <div className="mx-auto py-4 px-6">
        <div className="absolute l-0 top-9">{leftButton}</div>
        <div className="h-12 flex items-center justify-center">
          <h2 className="text-xl text-akvo-green font-semibold">AGRICONNECT</h2>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;
