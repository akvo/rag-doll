"use client";

import { useUserContext, useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { deleteCookie } from "@/lib/cookies";
import { BackIcon } from "@/utils/icons";
import { ChatHeader } from "@/components";
import { socket } from "@/lib";
import Image from "next/image";

const Account = () => {
  const user = useUserContext();
  const router = useRouter();
  const userDispatch = useUserDispatch();
  const authDispatch = useAuthDispatch();

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  const handleLogout = async () => {
    try {
      socket.disconnect();
      authDispatch({ type: "DELETE" });
      userDispatch({ type: "DELETE" });
      deleteCookie("AUTH_TOKEN");
      router.replace("/login");
    } catch (error) {
      console.error("Failed to logout:", error);
    }
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

      <div className="mt-44 p-4 bg-white flex flex-col justify-center">
        <div className="flex justify-center mb-6">
          <Image
            className="h-32 w-32 rounded-full bg-gray-300"
            width={32}
            height={32}
            alt="user"
            src="/images/bg-login-page.png"
          />
        </div>
        <div className="flex flex-col items-center space-y-6">
          <div className="text-2xl font-semibold font-assistant">
            {user.name || user.phone_number}
          </div>
          <div className="text-lg font-semibold font-assistant">
            EXTENSION OFFICER
          </div>
          <div className="text-lg font-semibold font-assistant">
            {user.phone_number}
          </div>
        </div>
        <div className="flex justify-center mt-6">
          <button
            onClick={handleLogout}
            className="font-assistant text-sm py-2 px-4 bg-white border border-red-500 hover:bg-red-600 text-red-500 hover:text-white font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Account;
