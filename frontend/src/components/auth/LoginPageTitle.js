"use client";

import { BackIcon } from "@/utils/icons";
import { useRouter } from "next/navigation";

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
  const router = useRouter();

  const handleOnClickBack = () => {
    router.replace("/");
  };

  return (
    <div className="flex flex-col flex-start w-full max-w-sm">
      <button className="mt-4 mb-20" onClick={handleOnClickBack}>
        <BackIcon />
      </button>
      <LoginTitle />
    </div>
  );
};

export default LoginPageTitle;
