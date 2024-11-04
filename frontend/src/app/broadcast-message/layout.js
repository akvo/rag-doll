import { ChatContextProvider, UserContextProvider } from "@/context";
import { ChatTabs } from "@/components";

const BroadcastMessageLayout = ({ children }) => {
  return (
    <UserContextProvider>
      <ChatContextProvider>
        {children}
        <ChatTabs />
      </ChatContextProvider>
    </UserContextProvider>
  );
};

export default BroadcastMessageLayout;
