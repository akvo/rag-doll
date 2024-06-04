"use client";
import { useAuthContext, useAuthDispatch } from "@/context/AuthContextProvider";

const Home = () => {
  const auth = useAuthContext();
  // const authDispatch = useAuthDispatch();

  // useEffect(() => {
  //   if (!auth.isLogin) {
  //     authDispatch({
  //       type: "UPDATE",
  //       payload: {
  //         token: "JWT",
  //       },
  //     });
  //   }
  // }, [auth.isLogins]);

  console.log(auth, "AUTH");

  return <h1 className="text-3xl font-bold underline">Home page</h1>;
};

export default Home;
