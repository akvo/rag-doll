"use client";

import { useEffect, useCallback } from "react";
import { useAuthContext, useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { api } from "@/lib";
import { setCookie } from "./util";

const VerifyLogin = ({ params }) => {
  const route = useRouter();
  const auth = useAuthContext();
  const authDispatch = useAuthDispatch();
  const userDispatch = useUserDispatch();

  const verifyUser = useCallback(async () => {
    if (!auth.isLogin) {
      const res = await api.get(`verify/${params.loginId}`);
      const resData = await res.json();
      if (resData && resData?.token) {
        setCookie("AUTH_TOKEN", resData.token);
        api.setToken(resData.token);
        setTimeout(() => {
          authDispatch({
            type: "UPDATE",
            payload: {
              token: resData.token,
              isLogin: true,
            },
          });
          userDispatch({
            type: "UPDATE",
            payload: {
              id: 1,
              name: "Test user",
              email: "test@test.com  ",
            },
          });
          route.replace("/chats");
        }, 1500);
      }
    }
  }, [auth.isLogin, params.loginId]);

  useEffect(() => {
    verifyUser();
  }, [verifyUser]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="flex flex-col items-center">
        <img
          className="h-16 w-16 mb-4"
          src="https://tailwindui.com/img/logos/mark.svg?color=indigo&shade=600"
          alt="Loading"
        />
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
