import { ChatContextProvider, UserContextProvider } from "@/context";
import { ChatTabs } from "@/components";

const AccountLayout = ({ children }) => {
  return (
    <UserContextProvider>
      <ChatContextProvider>
        {children}
        <ChatTabs />
      </ChatContextProvider>
    </UserContextProvider>
  );
};

export default AccountLayout;
