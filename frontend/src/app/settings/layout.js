import { UserContextProvider } from "@/context";

const SettingsLayout = ({ children }) => {
  return <UserContextProvider>{children}</UserContextProvider>;
};

export default SettingsLayout;
