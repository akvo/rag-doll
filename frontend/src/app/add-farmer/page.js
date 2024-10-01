"use client";

import { useRouter } from "next/navigation";
import { BackIcon } from "@/utils/icons";
import { ChatHeader } from "@/components";
import FarmerForm from "@/components/chats/FarmerForm";

const Account = () => {
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
      <FarmerForm />
    </div>
  );
};

export default Account;
