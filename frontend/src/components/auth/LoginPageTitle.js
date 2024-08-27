"use client";

import { usePathname } from "next/navigation";
import { BackIcon } from "@/utils/icons";

const LoginTitle = () => {
  return (
    <div>
      <h1 className="bg-akvo-green-100 w-auto text-akvo-green max-w-60">
        Welcome back 👋
      </h1>
      <p className="mt-4 info-text">
        Please enter your phone number to access your account
      </p>
    </div>
  );
};

const LoginPageTitle = () => {
  const pathname = usePathname();

  return (
    <div className="flex flex-col flex-start w-full max-w-sm mx-auto">
      <button className="mt-4 mb-20">
        <BackIcon />
      </button>
      {pathname.includes("login") ? (
        <LoginTitle />
      ) : (
        <h1 className="text-2xl">Sign up to join us</h1>
      )}
    </div>
  );
};

export default LoginPageTitle;
