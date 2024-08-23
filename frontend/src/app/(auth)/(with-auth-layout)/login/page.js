"use client";

import { useState } from "react";
import { api } from "@/lib";
import { Notification } from "@/components";
import "react-phone-number-input/style.css";
import PhoneInput, { isValidPhoneNumber } from "react-phone-number-input";
import { ButtonLoadingIcon } from "@/utils/icons";

const Login = () => {
  const [showNotification, setShowNotification] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");
  const [phoneNumber, setPhoneNumber] = useState(null);
  const [disabled, setDisabled] = useState(false);

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
    <div className="mt-10">
      <form className="space-y-6 mt-8 max-w-sm" onSubmit={handleSubmit}>
        <div>
          <label
            htmlFor="phone"
            className="block text-sm font-medium text-gray-900 font-assistant"
          >
            Phone Number
          </label>
          <div className="mt-2">
            <PhoneInput
              id="phone"
              name="phone"
              placeholder="Enter phone number"
              value={phoneNumber}
              onChange={setPhoneNumber}
              international
              defaultCountry="KE"
              initialValueFormat="international"
              className="block w-full rounded-md border-0 py-1.5 px-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-gray-500 sm:text-sm sm:leading-6"
            />
          </div>
        </div>

        <div>
          <button
            disabled={disabled}
            type="submit"
            className={`btn-login mt-96 flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 ${
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
