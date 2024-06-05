"use client";
import { usePathname } from "next/navigation";

const LoginPageTitle = () => {
  const pathname = usePathname();

  return (
    <div className="flex flex-col items-center w-full max-w-xs mx-auto">
      <img
        className="h-16 w-auto mt-10"
        src="https://tailwindui.com/img/logos/mark.svg?color=indigo&shade=600"
        alt="Your Company"
      />
      <h2 className="mt-6 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        {pathname.includes("login")
          ? "Sign in to your account"
          : "Sign up to join us"}
      </h2>
    </div>
  );
};

export default LoginPageTitle;
