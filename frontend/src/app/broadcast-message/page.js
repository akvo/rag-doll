"use client";

import "./style.css";
import { useRouter } from "next/navigation";
import { BackIcon } from "@/utils/icons";
import { ChatHeader, Notification } from "@/components";
import { useUserContext } from "@/context/UserContextProvider";
import { ButtonLoadingIcon } from "@/utils/icons";
import { useState, useMemo, useEffect } from "react";
import { api } from "@/lib";

const MAX_CHARACTERS = 1600;

const BroadcastMessage = () => {
  const router = useRouter();
  const { clients } = useUserContext();
  const [selectedClients, setSelectedClients] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [message, setMessage] = useState("");
  const [disabled, setDisabled] = useState(false);
  const [notificationContent, setNotificationContent] = useState("");
  const [showNotification, setShowNotification] = useState(false);
  const [searchClient, setSearchClient] = useState("");

  useEffect(() => {
    setSelectAll(selectedClients.length === clients.length);
  }, [clients, selectedClients]);

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  const handleClientChange = (clientId) => {
    setSelectedClients((prevSelectedClients) => {
      if (prevSelectedClients.includes(clientId)) {
        return prevSelectedClients.filter((id) => id !== clientId);
      } else {
        return [...prevSelectedClients, clientId];
      }
    });
    setSearchClient("");
  };

  const handleSearchClient = (event) => {
    setSearchClient(event.target.value);
  };

  const filteredClients = useMemo(() => {
    if (!searchClient) return clients;
    return clients.filter(
      (client) =>
        client.name.toLowerCase().includes(searchClient.toLowerCase()) ||
        client.phone_number.includes(searchClient)
    );
  }, [searchClient, clients]);

  const handleSelectAllChange = (event) => {
    const isChecked = event.target.checked;
    setSelectAll(isChecked);
    setSelectedClients(isChecked ? clients.map((client) => client.id) : []);
  };

  const handleMessageChange = (e) => {
    setMessage(e.target.value);
  };

  const handleShowNotification = () => {
    setShowNotification(true);
    setTimeout(() => {
      setShowNotification(false);
      setNotificationContent("");
    }, 3000);
  };

  const handleClearForm = () => {
    setMessage("");
    setSelectedClients([]);
    setSelectAll(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setDisabled(true);

    if (selectedClients.length === 0) {
      setNotificationContent("Please select at least one client.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    if (message.trim() === "") {
      setNotificationContent("Please enter a message.");
      handleShowNotification();
      setDisabled(false);
      return;
    }

    const requestData = {
      message,
      contacts: clients
        .filter((c) => selectedClients.includes(c.id))
        .map((c) => c.phone_number),
    };

    try {
      const response = await api.post(
        "send-broadcast",
        JSON.stringify(requestData)
      );
      if (response.status === 200) {
        setNotificationContent("Message sent successfully.");
        handleShowNotification();
        setTimeout(() => {
          setDisabled(false);
          handleClearForm();
        }, 1000);
      } else {
        setNotificationContent("Error, please try again later.");
        handleShowNotification();
        setDisabled(false);
      }
    } catch (error) {
      console.error("Error:", error);
      setNotificationContent(
        "There was an error sending the broadcast message. Please try again."
      );
      handleShowNotification();
      setDisabled(false);
    }
  };

  return (
    <div className="min-h-screen">
      <ChatHeader
        leftButton={
          <button onClick={handleOnClickBack}>
            <BackIcon />
          </button>
        }
      />
      <div className="flex justify-center min-h-screen bg-white mt-20">
        <form onSubmit={handleSubmit} className="p-10 w-full">
          <h2 className="text-lg font-semibold mb-10">
            Send Broadcast Message
          </h2>

          {/* Client List */}
          <div className="mb-8">
            <label className="block text-sm mb-2">Select Farmer</label>
            <div className="flex items-center mb-2">
              <input
                id="select-all-clients"
                type="checkbox"
                checked={selectAll}
                onChange={handleSelectAllChange}
                className="mr-2"
              />
              <label htmlFor="select-all-clients">Select All</label>
            </div>
            <input
              type="text"
              placeholder="Search farmer"
              className="w-full px-4 py-2 border rounded-lg text-md mb-2"
              onChange={handleSearchClient}
              value={searchClient}
            />
            <div
              className="w-full border rounded-lg p-2"
              style={{
                maxHeight: "110px",
                overflowY: "auto",
                backgroundColor: "white",
              }}
            >
              {filteredClients.map((client) => (
                <div key={client.id} className="flex items-center mb-1">
                  <input
                    type="checkbox"
                    id={`client-${client.id}`}
                    checked={selectedClients.includes(client.id)}
                    onChange={() => handleClientChange(client.id)}
                    className="mr-2"
                  />
                  <label htmlFor={`client-${client.id}`}>{client.name}</label>
                </div>
              ))}
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm mb-2">
              Message <span className="text-xs">(1600 characters max)</span>
            </label>
            <textarea
              rows={5}
              maxLength={MAX_CHARACTERS}
              value={message}
              onChange={handleMessageChange}
              required
              className="w-full px-4 py-2 border rounded-lg text-md resize-none overflow-auto"
            />
            <div className="text-right text-xs mt-1">
              {MAX_CHARACTERS - message.length} characters left
            </div>
          </div>

          {/* Submit Button */}
          <button
            disabled={disabled}
            type="submit"
            className={`w-full text-white rounded-md py-3 shadow-sm flex justify-center ${
              disabled
                ? "bg-akvo-green cursor-not-allowed"
                : "bg-akvo-green hover:bg-green-700 focus:ring-green-700"
            }`}
          >
            {disabled ? <ButtonLoadingIcon /> : "Send"}
          </button>
        </form>
      </div>

      <Notification message={notificationContent} show={showNotification} />
    </div>
  );
};

export default BroadcastMessage;
