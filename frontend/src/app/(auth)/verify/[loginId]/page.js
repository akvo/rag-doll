"use client";

import { useEffect } from "react";
import { useAuthContext, useAuthDispatch } from "@/context/AuthContextProvider";
import { useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";

const VerifyLogin = ({ params }) => {
  const route = useRouter();
  const auth = useAuthContext();
  const authDispatch = useAuthDispatch();
  const userDispatch = useUserDispatch();

  useEffect(() => {
    if (!auth.isLogin) {
      setTimeout(() => {
        authDispatch({
          type: "UPDATE",
          payload: {
            token: "Bearer token",
            isLogin: true,
          },
        });
        userDispatch({
          type: "UPDATE",
          payload: {
            id: 1,
            name: "Wayan",
            email: "test@test.com  ",
          },
        });
        route.replace("/");
      }, 500);
    }
  }, [auth.isLogin]);

  return <div>Verify {params.loginId}</div>;
};

export default VerifyLogin;
