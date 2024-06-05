const ChatTabs = () => {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-center items-center space-x-20 h-16">
          <button className="px-4 py-2 text-gray-600 hover:text-gray-800">
            Chats
          </button>
          <button className="px-4 py-2 text-gray-600 hover:text-gray-800">
            Reference
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatTabs;
