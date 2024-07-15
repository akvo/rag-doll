import { ChatContextProvider, UserContextProvider } from "@/context";
import { ChatTabs } from "@/components";

const ChatLayout = ({ children }) => {
  return (
    <UserContextProvider>
      <ChatContextProvider>
        <div className="flex h-screen bg-gray-100">{children}</div>
        <ChatTabs />
      </ChatContextProvider>
    </UserContextProvider>
  );
};

export default ChatLayout;
