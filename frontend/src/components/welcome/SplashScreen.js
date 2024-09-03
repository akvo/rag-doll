import React from "react";
import { AgriconnecetIcon } from "@/utils/icons";

const SplashScreen = () => {
  return (
    <div className="bg-splash-page h-screen overflow-hidden flex items-center justify-center">
      <div className="relative p-4 -mt-20">
        <div className="absolute inset-4 transform translate-x-2 translate-y-2 border-2 border-white"></div>
        <div className="relative bg-white p-6">
          <AgriconnecetIcon />
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
