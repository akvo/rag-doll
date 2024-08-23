"use client";

import { useChatContext, useChatDispatch } from "@/context/ChatContextProvider";
import { usePathname, useRouter } from "next/navigation";
import { ChatIcon, ReferenceIcon, AccountIcon } from "@/utils/icons";

const chatButtonType = (type) => {
  const { clientId } = useChatContext();
  const chatDispatch = useChatDispatch();
  const router = useRouter();
  const pathname = usePathname();

  switch (type) {
    case "chats":
      return {
        active: clientId ? false : true,
        icon: <ChatIcon />,
        text: "Chats",
        onClick: () => {
          chatDispatch({
            type: "CLEAR",
          });
        },
      };
    case "reference":
      return {
        active: pathname.includes("reference"),
        icon: <ReferenceIcon />,
        text: "Reference",
        onClick: () => {},
      };
    case "account":
      return {
        active: pathname.includes("account"),
        icon: <AccountIcon />,
        text: "Account",
        onClick: () => {},
      };
    default:
      throw Error(`Unknown tab type: ${type}.`);
  }
};

const ChatTabButton = ({ type }) => {
  const buttonEl = chatButtonType(type);

  return (
    <button
      className={`flex flex-col items-center px-4 py-2 justify-center ${
        buttonEl.active && type ? "text-akvo-green" : "text-gray-600"
      }  hover:text-green-600`}
      onClick={() => (buttonEl?.onClick ? buttonEl.onClick() : null)}
    >
      {buttonEl.icon}
      <div className="mt-1.5 text-sm">{buttonEl.text}</div>
    </button>
  );
};

export default ChatTabButton;
