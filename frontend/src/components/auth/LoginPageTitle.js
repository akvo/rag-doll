"use client";

import { usePathname } from "next/navigation";

const LoginTitle = () => {
  return (
    <div>
      <h2 className="bg-akvo-green-100 w-auto text-akvo-green">Welcome back</h2>
      <p className="mt-4 text-sm font-normal">
        Please enter your phone number to access your account
      </p>
    </div>
  );
};

const LoginPageTitle = () => {
  const pathname = usePathname();

  return (
    <div className="flex flex-col items-center w-full max-w-xs mx-auto">
      {pathname.includes("login") ? <LoginTitle /> : "Sign up to join us"}
    </div>
  );
};

export default LoginPageTitle;
