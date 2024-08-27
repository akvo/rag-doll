"use client";

import { useChatDispatch } from "@/context/ChatContextProvider";
import { usePathname, useRouter } from "next/navigation";
import { ChatIcon, ReferenceIcon, AccountIcon } from "@/utils/icons";

const chatButtonType = (type) => {
  const chatDispatch = useChatDispatch();
  const router = useRouter();
  const pathname = usePathname();

  switch (type) {
    case "chats":
      return {
        active: pathname.includes("chats"),
        icon: <ChatIcon />,
        text: "Chats",
        onClick: () => {
          chatDispatch({
            type: "CLEAR",
          });
          router.replace("/chats");
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
        onClick: () => {
          router.replace("/account");
        },
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
      }  hover:text-green-700`}
      onClick={() => (buttonEl?.onClick ? buttonEl.onClick() : null)}
    >
      {buttonEl.icon}
      <div
        className={`mt-1.5 text-sm  ${
          buttonEl.active && type ? "text-akvo-green" : "text-gray-600"
        }`}
      >
        {buttonEl.text}
      </div>
    </button>
  );
};

export default ChatTabButton;
