import { LoginPageTitle } from "@/components";

const AuthLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-login-page">
      <div className="flex min-h-full flex-col justify-center px-12 py-12 lg:px-8">
        <LoginPageTitle />
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">{children}</div>
      </div>
    </div>
  );
};

export default AuthLayout;
