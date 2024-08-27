"use client";

import { useEffect } from "react";
import { useUserContext, useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { deleteCookie } from "@/lib/cookies";
import { BackIcon } from "@/utils/icons";
import { ChatHeader } from "@/components";
import { api } from "@/lib";

const Account = () => {
  const user = useUserContext();
  const router = useRouter();
  const userDispatch = useUserDispatch();
  const authDispatch = useAuthDispatch();

  // get user me
  useEffect(() => {
    const fetchUserMe = async () => {
      const res = await api.get("me");
      if (res.status === 200) {
        const resData = await res.json();
        userDispatch({ type: "UPDATE", payload: { ...resData } });
      }
    };
    fetchUserMe();
  }, []);

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  const handleLogout = () => {
    // Clear user & auth context
    // Redirect to login page
    authDispatch({ type: "DELETE" });
    deleteCookie("AUTH_TOKEN");
    setTimeout(() => {
      userDispatch({
        type: "DELETE",
      });
      router.replace("/login");
    }, 500);
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

      <div className="p-4 bg-white mt-32">
        <div className="flex justify-center mb-6">
          <img
            className="h-32 w-32 rounded-full"
            src="https://via.placeholder.com/150"
            alt="User Avatar"
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
