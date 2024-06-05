import { ChatContextProvider } from "@/context";
import { ChatTabs } from "@/components";

const ChatLayout = ({ children }) => {
  return (
    <ChatContextProvider>
      <div className="flex h-screen bg-gray-100">{children}</div>
      <ChatTabs />
    </ChatContextProvider>
  );
};

export default ChatLayout;
