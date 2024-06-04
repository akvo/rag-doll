// import styles from "./page.module.css";
"use client";
import { useEffect } from "react";
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

  return <h1>Home page</h1>;
};

export default Home;
