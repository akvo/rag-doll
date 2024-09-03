"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

const slides = [
  {
    title: "The Best AI Farm Assistant",
    subtitle:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla porta massa felis, ut tempus eros faucibus.",
  },
  {
    title: "Manage your Farmer Conversations",
    subtitle:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla porta massa felis, ut tempus eros faucibus.",
  },
  {
    title: "Power up your communities",
    subtitle:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla porta massa felis, ut tempus eros faucibus.",
  },
];

const Welcome = () => {
  const router = useRouter();
  const [activeIndex, setActiveIndex] = useState(0);

  const handleDotClick = (index) => {
    setActiveIndex(index);
  };

  const handleOnClickNext = () => {
    if (activeIndex === slides.length - 1) {
      router.replace("/login");
      return;
    }
    setActiveIndex(activeIndex + 1);
  };

  const handleOnClickSkip = () => {
    router.replace("/login");
  };

  return (
    <div className="bg-login-page">
      <div className="relative flex items-center min-h-screen px-12 py-12 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="relative overflow-hidden -mt-24">
          {/* Sliding Text Container */}
          <div
            className="sliding-text-container min-h-40"
            style={{
              transform: `translateX(-${activeIndex * 33.33}%)`,
              width: `${slides.length * 100}%`,
            }}
          >
            {slides.map((it, index) => (
              <div key={index} className="w-full flex flex-col space-y-2">
                <h1 className="bg-akvo-green-100 w-auto text-akvo-green max-w-72">
                  {it.title}
                </h1>
                <p className="text-sm max-w-96">{it.subtitle}</p>
              </div>
            ))}
          </div>

          {/* Navigation Dots */}
          <div className="absolute bottom-0 left-0 w-full flex justify-start space-x-2">
            {slides.map((_, index) => (
              <div
                key={index}
                className={`h-2 rounded-full cursor-pointer ${
                  index === activeIndex
                    ? "bg-akvo-green w-5"
                    : "bg-gray-400 w-2"
                }`}
                onClick={() => handleDotClick(index)}
              ></div>
            ))}
          </div>
        </div>

        {/* Button */}
        <div className="absolute bottom-24 flex space-x-4">
          <button
            className="bg-gray-300 px-5 py-3 rounded-lg text-sm"
            onClick={handleOnClickSkip}
          >
            Skip
          </button>
          <button
            className="bg-akvo-green px-5 py-3 text-white rounded-lg text-sm"
            onClick={handleOnClickNext}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
