import { LoginPageTitle } from "@/components";

const AuthLayout = ({ children }) => {
  return (
    <div className="bg-login-page">
      <div className="relative min-h-screen px-12 py-12 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex flex-col justify-center">
          <LoginPageTitle />
          <div>{children}</div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
