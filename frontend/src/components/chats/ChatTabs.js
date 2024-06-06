import ChatTabButton from "./ChatTabButton";

const ChatTabs = () => {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-center items-center space-x-20 h-16">
          <ChatTabButton type="chats" />
          <ChatTabButton type="reference" />
          <ChatTabButton type="settings" />
        </div>
      </div>
    </div>
  );
};

export default ChatTabs;
