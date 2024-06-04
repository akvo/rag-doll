"use client";
import { usePathname } from "next/navigation";

const LoginPageTitle = () => {
  const pathname = usePathname();

  return (
    <div className="sm:mx-auto sm:w-full sm:max-w-sm">
      <img
        className="mx-auto h-10 w-auto"
        src="https://tailwindui.com/img/logos/mark.svg?color=indigo&shade=600"
        alt="Your Company"
      />
      <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        {pathname.includes("login")
          ? "Sign in to your account"
          : "Sign up to join us"}
      </h2>
    </div>
  );
};

export default LoginPageTitle;
