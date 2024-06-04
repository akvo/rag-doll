import { UserContextProvider } from "@/context";

const VerifyLayout = ({ children }) => {
  return <UserContextProvider>{children}</UserContextProvider>;
};

export default VerifyLayout;
