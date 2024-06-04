"use client";
import { useUserContext } from "@/context/UserContextProvider";

const Settings = () => {
  const user = useUserContext();
  console.log(user, "USER");

  return <div>Settings</div>;
};

export default Settings;
