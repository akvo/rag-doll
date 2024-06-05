const ChatSidebar = ({ isSidebarOpen }) => {
  return (
    <div
      className={`relative ${
        isSidebarOpen ? "w-1/4" : "hidden"
      } bg-gray-800 text-white p-4 overflow-hidden transition-all duration-300`}
    >
      {/* Sidebar Header */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-2">
          <img
            src="https://via.placeholder.com/50"
            alt="User Avatar"
            className="rounded-full"
          />
          <div>
            <h2 className="text-lg font-semibold">Username</h2>
            <p className="text-sm">Status</p>
          </div>
        </div>
      </div>
      {/* Sidebar Navigation */}
      <nav>
        <ul>
          <li className="mb-2">
            <a
              href="#"
              className="flex items-center px-4 py-2 text-gray-200 hover:bg-gray-700 rounded"
            >
              <span>Chats</span>
            </a>
          </li>
          <li className="mb-2">
            <a
              href="#"
              className="flex items-center px-4 py-2 text-gray-200 hover:bg-gray-700 rounded"
            >
              <span>Contacts</span>
            </a>
          </li>
          <li className="mb-2">
            <a
              href="#"
              className="flex items-center px-4 py-2 text-gray-200 hover:bg-gray-700 rounded"
            >
              <span>Settings</span>
            </a>
          </li>
        </ul>
      </nav>
    </div>
  );
};

export default ChatSidebar;
