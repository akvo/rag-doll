"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib";
import { Notification } from "@/components";
import "react-phone-number-input/style.css";
import PhoneInput, { isValidPhoneNumber } from "react-phone-number-input";

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
      return;
    }

    if (!isValidPhoneNumber(phoneNumber)) {
      setNotificationContent("Invalid phone number.");
      handleShowNotification();
      return;
    }

    try {
      const res = await api.post(
        `login?phone_number=${encodeURIComponent(phoneNumber)}`
      );
      const resData = await res.json();
      if (res.status === 200) {
        setNotificationContent(
          "Verification link sent to your WhatsApp. Please use it to verify your login."
        );
        handleShowNotification();
      } else if (res.status === 404) {
        setNotificationContent("Phone number not found.");
        handleShowNotification();
      } else {
        setNotificationContent("notificationContent, please try again later.");
        handleShowNotification();
      }
      setDisabled(false);
    } catch (notificationContent) {
      setNotificationContent("notificationContent, please try again later.");
      handleShowNotification();
      setDisabled(false);
    }
  };

  return (
    <>
      <form className="space-y-6 mt-8 mx-4" onSubmit={handleSubmit}>
        <div>
          <label
            htmlFor="phone"
            className="block text-sm font-medium text-gray-900"
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
            className={`flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              disabled
                ? "bg-green-300 cursor-not-allowed"
                : "bg-green-500 hover:bg-green-600 focus:ring-green-500"
            }`}
          >
            {disabled ? (
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zM12 24c6.627 0 12-5.373 12-12h-4a8 8 0 01-8 8v4z"
                ></path>
              </svg>
            ) : (
              "Sign in"
            )}
          </button>
        </div>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Not a member?
        <Link
          href="/register"
          className="font-semibold text-green-500 hover:text-green-600 ml-2"
        >
          Register
        </Link>
      </p>

      <Notification message={notificationContent} show={showNotification} />
    </>
  );
};

export default Login;
