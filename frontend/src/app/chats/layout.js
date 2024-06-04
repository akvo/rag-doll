import { ChatContextProvider } from "@/context";

const ChatLayout = ({ children }) => {
  return <ChatContextProvider>{children}</ChatContextProvider>;
};

export default ChatLayout;
