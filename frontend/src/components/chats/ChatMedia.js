import React, { useState } from "react";
import Image from "next/image";

const ChatMedia = ({ type, url }) => {
  const [selectedImage, setSelectedImage] = useState(null);

  const handleImageClick = (url) => {
    setSelectedImage(url); // Open modal with selected image
  };

  const closeModal = () => {
    setSelectedImage(null); // Close modal
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
          <Image
            width={225}
            height={175}
            src={url}
            alt={url}
            className="rounded-md shadow-sm mb-1 cursor-pointer"
            onClick={() => handleImageClick(url)}
            quality={75}
          />
        </div>
        {/* Image Modal */}
        {selectedImage && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75"
            onClick={handleModalClick}
          >
            <div className="relative w-full">
              <Image
                width={375}
                height={250}
                layout="responsive"
                src={selectedImage}
                alt="Full Image"
                className="max-w-full max-h-full"
                style={{
                  objectFit: "cover",
                }}
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
