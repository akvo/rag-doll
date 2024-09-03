"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib";
import { Notification } from "@/components";
import "react-phone-number-input/style.css";
import PhoneInput, { isValidPhoneNumber } from "react-phone-number-input";
import { ButtonLoadingIcon, PhoneIcon } from "@/utils/icons";

const Login = () => {
  const [showNotification, setShowNotification] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");
  const [phoneNumber, setPhoneNumber] = useState(null);
  const [disabled, setDisabled] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Check localStorage on component mount
  useEffect(() => {
    const savedPhoneNumber = localStorage.getItem("phoneNumber");
    const savedPreference = localStorage.getItem("rememberMe") === "true";
    setPhoneNumber(savedPhoneNumber || null);
    setRememberMe(savedPreference);
  }, []);

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNotificationContent("");
    }, 3000);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setDisabled(true);

    if (!phoneNumber) {
      setNotificationContent("Phone number required.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    if (!isValidPhoneNumber(phoneNumber)) {
      setNotificationContent("Invalid phone number.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    try {
      const res = await api.post(
        `login?phone_number=${encodeURIComponent(phoneNumber)}`
      );
      if (res.status === 200) {
        setNotificationContent(
          "Verification link sent to your WhatsApp. Please use it to verify your login."
        );
        handleShowNotification();

        // Store phone number and preference in local storage if "Remember me" is checked
        if (rememberMe) {
          localStorage.setItem("phoneNumber", phoneNumber);
          localStorage.setItem("rememberMe", "true");
        } else {
          localStorage.removeItem("phoneNumber");
          localStorage.removeItem("rememberMe");
        }
      } else if (res.status === 404) {
        setNotificationContent("Phone number not found.");
        handleShowNotification();
      } else {
        setNotificationContent("Error, please try again later.");
        handleShowNotification();
      }
      setDisabled(false);
    } catch (error) {
      setNotificationContent("Error, please try again later.");
      handleShowNotification();
      setDisabled(false);
    }
  };

  return (
    <div className="mt-20">
      <form className="space-y-6 mt-5" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="phone" className="block">
            Phone Number
          </label>
          <div className="mt-2 flex border-b-2 border-gray-400 items-center">
            <PhoneInput
              id="phone"
              name="phone"
              placeholder="Enter phone number"
              value={phoneNumber}
              onChange={setPhoneNumber}
              international
              defaultCountry="KE"
              initialValueFormat="international"
              className="block w-full p-2 text-gray-600 font-medium"
            />
            <PhoneIcon />
          </div>
        </div>
        <div className="mt-2">
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            <div className="w-5 h-5 border-2 border-gray-300 rounded-md flex items-center justify-center bg-white relative peer-checked:bg-akvo-green">
              <div className="absolute inset-0 flex items-center justify-center peer-checked:block">
                <span className="text-white text-sm">✔</span>
              </div>
            </div>
            <span className="ml-2">Remember me</span>
          </label>
        </div>

        {/* Button container with absolute positioning */}
        <div className="absolute left-0 bottom-24 w-full px-12">
          <button
            disabled={disabled}
            type="submit"
            className={`btn-login flex w-full justify-center rounded-md px-3 py-2 text-sm sm:text-base font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              disabled
                ? "bg-akvo-green cursor-not-allowed"
                : "bg-akvo-green hover:bg-green-700 focus:ring-green-700"
            }`}
          >
            {disabled ? <ButtonLoadingIcon /> : "Log in"}
          </button>
        </div>
      </form>

      <Notification message={notificationContent} show={showNotification} />
    </div>
  );
};

export default Login;
