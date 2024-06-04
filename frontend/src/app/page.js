// import styles from "./page.module.css";
"use client";
import { useToken } from "@/context/TokenContextProvider";

const Home = () => {
  const { token, setToken } = useToken();
  console.log(token, setToken, "===");

  return <h1>Home / Login page</h1>;
};

export default Home;
