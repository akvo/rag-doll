"use client";

import { useRouter } from "next/navigation";
import { BackIcon } from "@/utils/icons";
import { ChatHeader } from "@/components";
import { useUserContext } from "@/context/UserContextProvider";
import { ButtonLoadingIcon } from "@/utils/icons";
import { useState } from "react";

const MAX_CHARACTERS = 1600;

const BroadcastMessage = () => {
  const router = useRouter();
  const { clients } = useUserContext();
  const [selectedClients, setSelectedClients] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [message, setMessage] = useState("");
  const disabled = false;

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  const handleClientChange = (event) => {
    const value = Array.from(event.target.options)
      .filter((option) => option.selected)
      .map((option) => option.value);
    setSelectedClients(value);
    // Update selectAll state
    setSelectAll(value.length === clients.length);
  };

  const handleSelectAllChange = (event) => {
    const isChecked = event.target.checked;
    setSelectAll(isChecked);
    if (isChecked) {
      setSelectedClients(clients.map((client) => client.id));
    } else {
      setSelectedClients([]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO :: Add your submission logic here
  };

  const handleMessageChange = (e) => {
    setMessage(e.target.value);
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
        <form onSubmit={(e) => handleSubmit(e)} className="p-10 w-full">
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
            <select
              multiple
              value={selectedClients}
              onChange={handleClientChange}
              className="w-full border rounded-lg p-2"
              required
            >
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </select>
          </div>
          <div className="mb-8">
            <label className="block text-sm mb-2">
              Message <span className="text-xs">(1600 characters max)</span>
            </label>
            <textarea
              rows={7}
              maxLength={MAX_CHARACTERS}
              value={message}
              onChange={handleMessageChange}
              required
              className="w-full px-4 py-2 border rounded-lg resize-none overflow-auto tex-md"
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
    </div>
  );
};

export default BroadcastMessage;
