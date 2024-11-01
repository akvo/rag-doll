"use client";

import { useState } from "react";
import PhoneInput, { isValidPhoneNumber } from "react-phone-number-input";
import "react-phone-number-input/style.css";
import { ButtonLoadingIcon, PhoneIcon } from "@/utils/icons";
import Notification from "../utils/Notification";
import { useRouter } from "next/navigation";
import { api } from "@/lib";

const FarmerForm = ({
  isEdit = false,
  clientId = null,
  clientName = null,
  clientPhoneNumber = null,
  chatDispatch = () => {},
}) => {
  const [farmerName, setFarmerName] = useState(clientName);
  const [phoneNumber, setPhoneNumber] = useState(clientPhoneNumber);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");
  const [disabled, setDisabled] = useState(false);
  const router = useRouter();

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNotificationContent("");
    }, 3000);
  };

  const handleSubmit = async (e) => {
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

    const payload = new FormData();
    payload.append("name", farmerName);
    payload.append("phone_number", phoneNumber);

    try {
      const res = await api.post("client", payload);
      if (res.status === 200) {
        setNotificationContent("Farmer registered successfully.");
        handleShowNotification();
        setTimeout(() => {
          setDisabled(false);
          router.replace("/chats");
        }, 1000);
        return;
      } else if (res.status === 409) {
        const response = await res.json();
        setNotificationContent(
          `Farmer ${phoneNumber} already registered. Forwarding to chat window.`
        );
        handleShowNotification();
        if (response?.detail?.id) {
          // TODO :: when add existing farmer we should check if that farmer chat_session is same with logged in user
          // if yes, forward to conversation
          // if no, popup a notification that say farmer is handled by another officer
          const { detail: selectedClient } = response;
          localStorage.setItem(
            "selectedClient",
            JSON.stringify(selectedClient)
          );
          setTimeout(() => {
            setDisabled(false);
            router.back();
          }, 1000);
        }
      } else {
        setNotificationContent("Error, please try again later.");
        handleShowNotification();
        setDisabled(false);
      }
    } catch (error) {
      setNotificationContent("Error, please try again later.");
      handleShowNotification();
      setDisabled(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setDisabled(true);

    if (!farmerName) {
      setNotificationContent("Please fill farmer's name.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    try {
      const res = await api.put(`client/${clientId}?name=${farmerName}`);
      if (res.status === 200) {
        setNotificationContent("Farmer updated successfully.");
        handleShowNotification();
        chatDispatch({ type: "UPDATE", payload: { clientName: farmerName } });
        setTimeout(() => {
          setDisabled(false);
        }, 1000);
        return;
      } else {
        setNotificationContent("Error, please try again later.");
        handleShowNotification();
        setDisabled(false);
      }
    } catch (error) {
      setNotificationContent("Error, please try again later.");
      handleShowNotification();
      setDisabled(false);
    }
  };

  return (
    <div
      className={`flex justify-center min-h-screen bg-white ${
        isEdit ? "mt-20" : "mt-28"
      }`}
    >
      <form
        onSubmit={(e) => (isEdit ? handleUpdate(e) : handleSubmit(e))}
        className="p-10 w-full"
      >
        <h2 className="text-lg font-semibold mb-10">
          {isEdit ? "Update" : "Add"} Farmer
        </h2>
        {/* Farmer Name Field */}
        <div className="mb-8">
          <label className="block text-sm mb-2">Farmer Name</label>
          <input
            type="text"
            value={farmerName || ""}
            onChange={(e) => setFarmerName(e.target.value)}
            placeholder="Enter farmer's name"
            className="w-full px-4 py-2 border-gray-400 border-b text-md"
          />
        </div>

        {/* Phone Number Field */}
        <div className="mb-10">
          <label className="block text-sm mb-2">Phone Number</label>
          <div
            className={`mt-2 flex items-center ${
              !isEdit ? "border-b border-gray-400" : ""
            }`}
          >
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
              disabled={isEdit}
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
          {disabled ? <ButtonLoadingIcon /> : "Save"}
        </button>
      </form>

      <Notification message={notificationContent} show={showNotification} />
    </div>
  );
};

export default FarmerForm;
