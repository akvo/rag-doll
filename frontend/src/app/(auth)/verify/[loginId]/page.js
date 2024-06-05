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
      }, 1500);
    }
  }, [auth.isLogin]);

  return (
    <div className="flex items-center justify-center h-screen">
      <div
        className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-e-transparent align-[-0.125em] text-primary motion-reduce:animate-[spin_1.5s_linear_infinite] text-blue-300"
        role="status"
      >
        <span className="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">
          Verifying {params.id}...
        </span>
      </div>
    </div>
  );
};

export default VerifyLogin;
