"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib";
import { Notification } from "@/components";
import "react-phone-number-input/style.css";
import PhoneInput, { isValidPhoneNumber } from "react-phone-number-input";

const Login = () => {
  const router = useRouter();
  const [showNotification, setShowNotification] = useState(false);
  const [error, setError] = useState("");
  const [phoneNumber, setPhoneNumber] = useState(null);

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setError("");
    }, 1000);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!phoneNumber) {
      setError("Phone number required.");
      handleShowNotification();
      return;
    }

    if (!isValidPhoneNumber(phoneNumber)) {
      setError("Invalid phone number.");
      handleShowNotification();
      return;
    }

    try {
      const res = await api.post(
        `login?phone_number=${encodeURIComponent(phoneNumber)}`
      );
      const resData = await res.json();
      if (res.status === 200) {
        const regex = /https?:\/\/[^\/]+(\/.+)/;
        const match = resData.match(regex);
        if (match && match[1]) {
          // TODO :: Here we should not navigate to verify, user will clik the link from a message they received
          router.replace(match[1]);
        }
      } else if (res.status === 404) {
        setError("Phone number not found.");
        handleShowNotification();
      } else {
        setError("Error, please try again later.");
        handleShowNotification();
      }
    } catch (error) {
      setError("Error, please try again later.");
      handleShowNotification();
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
            type="submit"
            className="flex w-full justify-center rounded-md bg-green-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            Sign in
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

      <Notification message={error} show={showNotification} />
    </>
  );
};

export default Login;
