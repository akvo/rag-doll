import { LoginPageTitle } from "@/components";

const AuthLayout = ({ children }) => {
  return (
    <div className="relative min-h-screen bg-login-page px-12 py-12 sm:mx-auto sm:w-full sm:max-w-sm">
      <div className="flex flex-col justify-center">
        <LoginPageTitle />
        <div>{children}</div>
      </div>
    </div>
  );
};

export default AuthLayout;
