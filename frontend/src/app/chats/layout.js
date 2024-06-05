import { ChatContextProvider } from "@/context";

const ChatLayout = ({ children }) => {
  return (
    <ChatContextProvider>
      <div className="flex h-screen bg-gray-100">{children}</div>
    </ChatContextProvider>
  );
};

export default ChatLayout;
