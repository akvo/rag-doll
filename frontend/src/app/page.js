"use client";

import { useEffect, useState } from "react";
import { SplashScreen, Welcome } from "@/components";

const Home = () => {
  const [isSplash, setIsSplash] = useState(true);
  const [fadeClass, setFadeClass] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      setFadeClass("fade-out");
      setTimeout(() => {
        setIsSplash(false);
        setFadeClass("fade-in");
      }, 500); // Match the fade-out duration
    }, 550); // Duration of the splash screen

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={fadeClass}>{isSplash ? <SplashScreen /> : <Welcome />}</div>
  );
};

export default Home;
