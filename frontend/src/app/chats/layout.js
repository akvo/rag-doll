import {
  ChatContextProvider,
  UserContextProvider,
  SocketContextProvider,
} from "@/context";
import { ChatTabs } from "@/components";

const ChatLayout = ({ children }) => {
  return (
    <UserContextProvider>
      <SocketContextProvider>
        <ChatContextProvider>
          <div className="flex h-screen bg-gray-100">{children}</div>
          <ChatTabs />
        </ChatContextProvider>
      </SocketContextProvider>
    </UserContextProvider>
  );
};

export default ChatLayout;
