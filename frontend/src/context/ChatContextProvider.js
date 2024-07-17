"use client";
import { createContext, useContext, useReducer } from "react";

const ChatContext = createContext(null);
const ChatDispatchContext = createContext(null);

const initialChatState = {
  clientName: null,
  clientPhoneNumber: null,
};

const chatReducer = (state, action) => {
  switch (action.type) {
    case "UPDATE":
      return {
        ...state,
        ...action.payload,
      };
    case "CLEAR":
      return initialChatState;
    default:
      throw Error(
        `Unknown action: ${action.type}. Remeber action type must be CAPITAL text.`
      );
  }
};

const ChatContextProvider = ({ children }) => {
  const [chat, dispatch] = useReducer(chatReducer, initialChatState);

  return (
    <ChatContext.Provider value={chat}>
      <ChatDispatchContext.Provider value={dispatch}>
        {children}
      </ChatDispatchContext.Provider>
    </ChatContext.Provider>
  );
};

export const useChatContext = () => useContext(ChatContext);

export const useChatDispatch = () => useContext(ChatDispatchContext);

export default ChatContextProvider;
