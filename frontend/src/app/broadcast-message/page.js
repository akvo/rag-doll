"use client";

import { useRouter } from "next/navigation";
import { BackIcon } from "@/utils/icons";
import { ChatHeader } from "@/components";

const BroadcastMessage = () => {
  const router = useRouter();

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  return (
    <div className="min-h-screen">
      <ChatHeader
        leftButton={
          <button onClick={handleOnClickBack}>
            <BackIcon />
          </button>
        }
      />
      <h1>Broadcast</h1>
    </div>
  );
};

export default BroadcastMessage;
