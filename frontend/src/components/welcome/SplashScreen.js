import React from "react";
import { AgriconnecetIcon } from "@/utils/icons";

const SplashScreen = () => {
  return (
    <div className="bg-splash-page">
      <div className="flex justify-center items-center min-h-screen px-12 py-12 sm:mx-auto sm:w-full sm:max-w-md">
        <div class="relative p-4">
          <div class="absolute inset-4 transform translate-x-2 translate-y-2 border-2 border-white"></div>
          <div class="relative bg-white p-6">
            <AgriconnecetIcon />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
