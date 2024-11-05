"use client";

import React, { useState, useRef, useEffect } from "react";
import { ThreeDotIcon } from "@/utils/icons";
import Notification from "../utils/Notification";

const ChatHeader = ({ leftButton, rightMenu = true }) => {
  const dropdownRef = useRef(null);
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNotificationContent("");
    }, 3000);
  };

  const copyToClipboard = (url) => {
    url = `${location.origin}${url}`;
    navigator.clipboard
      .writeText(url)
      .then(() => {
        setNotificationContent("Data Retention Policy URL copied.");
        handleShowNotification();
      })
      .catch((error) => {
        console.error("Failed to copy: ", error);
      });
  };

  // Close the dropdown if clicked outside
  const handleClickOutside = (event) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
      setDropdownOpen(false);
    }
  };

  useEffect(() => {
    // Add event listener to detect clicks outside
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      // Cleanup the event listener on component unmount
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 bg-gray-100 z-10 px-2 border-b border-gray-100">
      <div className="flex items-center justify-between mx-auto px-2 py-4">
        <div className="flex-start">{leftButton}</div>
        <h2 className="h-10  flex-grow text-center text-xl text-akvo-green font-semibold flex items-center justify-center">
          AGRICONNECT
        </h2>

        {rightMenu ? (
          <div className="flex-end">
            <button
              className="flex-end"
              onClick={() => setDropdownOpen((prev) => !prev)}
            >
              <ThreeDotIcon />
            </button>
          </div>
        ) : (
          ""
        )}
        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div
            ref={dropdownRef}
            className="absolute right-0 mt-24 mr-4 w-48 bg-white border rounded shadow-lg z-20"
          >
            <ul className="py-1">
              <li
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                onClick={() => {
                  setDropdownOpen(false);
                  copyToClipboard("/data-retention-policy");
                }}
              >
                Data Retention Policy
              </li>
            </ul>
          </div>
        )}
      </div>

      <Notification message={notificationContent} show={showNotification} />
    </div>
  );
};

export default ChatHeader;
