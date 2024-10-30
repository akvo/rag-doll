"use client";

import { useRouter } from "next/navigation";
import { BackIcon } from "@/utils/icons";
import { ChatHeader } from "@/components";
import { useUserContext } from "@/context/UserContextProvider";

const BroadcastMessage = () => {
  const router = useRouter();
  const { clients } = useUserContext();

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  console.log(clients, "TEST");

  // TODO :: Need the client list here

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
