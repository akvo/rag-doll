"use client";

import { useState } from "react";
import PhoneInput, { isValidPhoneNumber } from "react-phone-number-input";
import "react-phone-number-input/style.css";
import { ButtonLoadingIcon, PhoneIcon } from "@/utils/icons";
import Notification from "../utils/Notification";

const FarmerForm = () => {
  const [farmerName, setFarmerName] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState(null);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");
  const [disabled, setDisabled] = useState(false);

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNotificationContent("");
    }, 3000);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setDisabled(true);

    if (!farmerName && !phoneNumber) {
      setNotificationContent("Please fill farmer's name & phone number.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    if (!farmerName && phoneNumber) {
      setNotificationContent("Farmer's name required.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    if (!phoneNumber && farmerName) {
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

    setFarmerName("");
    setPhoneNumber("");
  };

  return (
    <div className="flex justify-center mt-28 min-h-screen bg-white">
      <form onSubmit={handleSubmit} className="p-10 max-w-md w-full">
        <h2 className="text-lg font-semibold mb-10">Add Farmer</h2>
        {/* Farmer Name Field */}
        <div className="mb-8">
          <label className="block text-sm mb-2">Farmer Name</label>
          <input
            type="text"
            value={farmerName}
            onChange={(e) => setFarmerName(e.target.value)}
            placeholder="Enter farmer's name"
            className="w-full px-4 py-2 border-gray-400 border-b text-md"
          />
        </div>

        {/* Phone Number Field */}
        <div className="mb-10">
          <label className="block text-sm mb-2">Phone Number</label>
          <div className="mt-2 flex border-b border-gray-400 items-center">
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

        {/* Submit Button */}
        <button
          disabled={disabled}
          type="submit"
          className={`w-full text-white py-2 rounded-md py-3 shadow-sm flex justify-center ${
            disabled
              ? "bg-akvo-green cursor-not-allowed"
              : "bg-akvo-green hover:bg-green-700 focus:ring-green-700"
          }`}
        >
          {disabled ? <ButtonLoadingIcon /> : "Add Farmer"}
        </button>
      </form>

      <Notification message={notificationContent} show={showNotification} />
    </div>
  );
};

export default FarmerForm;
