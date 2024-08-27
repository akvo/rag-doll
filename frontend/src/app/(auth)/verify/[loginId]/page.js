"use client";

import { useEffect, useCallback } from "react";
import { useAuthContext, useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserContext, useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { api } from "@/lib";
import { setCookie } from "@/lib/cookies";

const VerifyLogin = ({ params }) => {
  const route = useRouter();
  const auth = useAuthContext();
  const authDispatch = useAuthDispatch();
  const user = useUserContext();
  const userDispatch = useUserDispatch();

  const verifyUser = useCallback(async () => {
    if (!auth.isLogin && !user.id) {
      const res = await api.get(`verify/${params.loginId}`);
      const resData = await res.json();
      if (resData && resData?.token) {
        const { token, phone_number, name, id: userID } = resData;
        setCookie("AUTH_TOKEN", token);
        api.setToken(resData.token);
        authDispatch({
          type: "UPDATE",
          payload: {
            token,
            isLogin: true,
          },
        });
        userDispatch({
          type: "UPDATE",
          payload: {
            id: userID,
            name,
            phone_number,
          },
        });
        setTimeout(() => {
          route.replace("/chats");
        }, 1000);
      }
    }
  }, [auth.isLogin, params.loginId, user.id]);

  useEffect(() => {
    verifyUser();
  }, [verifyUser]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="flex flex-col items-center">
        <h2 className="text-lg font-semibold text-gray-800 mb-2">Verifying</h2>
        <p className="text-sm text-gray-600 mb-4">Please wait a moment...</p>
        <div className="flex items-center justify-center space-x-2">
          <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce"></div>
          <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce delay-150"></div>
          <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-bounce delay-300"></div>
        </div>
      </div>
    </div>
  );
};

export default VerifyLogin;
