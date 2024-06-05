const ChatWindow = () => {
  return (
    <div className="w-full bg-gray-200 flex">
      {/* Chat Header */}
      <div className="flex items-center p-4 bg-white border-b">
        <img
          src="https://via.placeholder.com/40"
          alt="User Avatar"
          className="rounded-full mr-4"
        />
        <div>
          <h3 className="text-lg font-semibold">Chat 1</h3>
          <p className="text-sm text-gray-600">Online</p>
        </div>
      </div>
      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-scroll">
        <div className="flex mb-4">
          <img
            src="https://via.placeholder.com/40"
            alt="User Avatar"
            className="rounded-full mr-4"
          />
          <div>
            <p className="bg-white p-4 rounded shadow">Hello!</p>
            <p className="text-sm text-gray-600 mt-1">10:00 AM</p>
          </div>
        </div>
        {/* Repeat for other messages */}
      </div>
      {/* Input */}
      <div className="p-4 bg-white border-t">
        <input
          type="text"
          placeholder="Type a message..."
          className="w-full px-4 py-2 border rounded"
        />
      </div>
    </div>
  );
};

export default ChatWindow;
