// import styles from "./page.module.css";
"use client";
import { useEffect } from "react";
import { useAuthContext, useAuthDispatch } from "@/context/AuthContextProvider";

const Home = () => {
  const auth = useAuthContext();
  const authDispatch = useAuthDispatch();

  useEffect(() => {
    if (!auth.token) {
      authDispatch({
        type: "UPDATE",
        payload: {
          token: "JWT",
        },
      });
    }
  }, [auth.token]);

  console.log(auth, "AUTH");

  return <h1>Home / Login page</h1>;
};

export default Home;
