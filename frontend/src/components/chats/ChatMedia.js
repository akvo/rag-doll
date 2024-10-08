import React, { useState } from "react";
import Image from "next/image";

const LoadingSpinner = () => (
  <div className="flex justify-center items-center w-full h-full">
    <div className="w-6 h-6 border-2 border-green-500 border-t-transparent border-solid rounded-full animate-spin"></div>
  </div>
);

const ChatMedia = ({ type, url }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  const handleImageClick = (url) => {
    setIsLoading(true);
    setSelectedImage(url);
  };

  const closeModal = () => {
    setSelectedImage(null);
  };

  const handleModalClick = (e) => {
    // Close the modal if clicked outside the image (on the background)
    if (e.target === e.currentTarget) {
      closeModal();
    }
  };

  if (type.includes("image")) {
    return (
      <>
        <div className="mt-2">
          {isLoading && <LoadingSpinner />}
          <Image
            width={isLoading ? 0 : 225}
            height={isLoading ? 0 : 175}
            src={url}
            alt={type}
            className="rounded-md shadow-sm mb-1 cursor-pointer"
            onClick={() => handleImageClick(url)}
            quality={75}
            style={{
              width: "auto",
              height: "auto",
            }}
            onLoad={handleImageLoad}
          />
        </div>
        {/* Image Modal */}
        {selectedImage && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75"
            onClick={handleModalClick}
          >
            <div className="relative w-full">
              {isLoading && <LoadingSpinner />}
              <Image
                src={selectedImage}
                alt="Full Image"
                sizes="100vw"
                style={{
                  width: "100%",
                  height: "auto",
                }}
                width={isLoading ? 0 : 500}
                height={isLoading ? 0 : 300}
                onLoad={handleImageLoad}
              />
            </div>
            <button
              className="absolute top-2 right-4 text-white text-lg"
              onClick={closeModal}
            >
              ✕
            </button>
          </div>
        )}
      </>
    );
  }

  return null;
};

export default ChatMedia;
