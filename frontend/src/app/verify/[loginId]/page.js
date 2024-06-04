"use client";
import { useUserContext } from "@/context/UserContextProvider";

const VerifyLogin = ({ params }) => {
  const user = useUserContext();
  console.log(user, "USER");

  return <div>Verify {params.loginId}</div>;
};

export default VerifyLogin;
