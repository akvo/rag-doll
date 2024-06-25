"use client";
import { useUserContext, useUserDispatch } from "@/context/UserContextProvider";
import { useRouter } from "next/navigation";
import { useAuthDispatch } from "@/context/AuthContextProvider";
import { deleteCookie } from "../(auth)/verify/[loginId]/util";

const Settings = () => {
  const user = useUserContext();
  const router = useRouter();
  const userDispatch = useUserDispatch();
  const authDispatch = useAuthDispatch();

  const handleOnClickBack = () => {
    router.replace("/chats");
  };

  const handleLogout = () => {
    // Clear user & auth context
    // Redirect to login page
    userDispatch({
      type: "DELETE",
    });
    authDispatch({ type: "DELETE" });
    deleteCookie("AUTH_TOKEN");
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="sticky top-0 bg-white shadow-md p-4">
        <div className="flex items-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-6 h-6 text-gray-800 cursor-pointer"
            onClick={handleOnClickBack}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15.75 19.5L8.25 12l7.5-7.5"
            />
          </svg>
          <h2 className="ml-4 text-xl text-gray-800">Profile</h2>
        </div>
      </div>
      <div className="p-4">
        <div className="flex justify-center mb-6">
          <img
            className="h-32 w-32 rounded-full"
            src="https://via.placeholder.com/150"
            alt="User Avatar"
          />
        </div>
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700"
            >
              Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              defaultValue="John Doe"
              className="mt-1 py-1.5 px-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50"
            />
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label
              htmlFor="status"
              className="block text-sm font-medium text-gray-700"
            >
              Status
            </label>
            <input
              id="status"
              name="status"
              type="text"
              defaultValue="Hey there!"
              className="mt-1 py-1.5 px-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50"
            />
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <label
              htmlFor="phone"
              className="block text-sm font-medium text-gray-700"
            >
              Phone
            </label>
            <input
              id="phone"
              name="phone"
              type="text"
              defaultValue="+123 456 7890"
              className="mt-1 py-1.5 px-2 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring focus:ring-green-500 focus:ring-opacity-50"
            />
          </div>
        </div>
        <div className="mt-6">
          <button
            onClick={handleLogout}
            className="w-full py-2 px-4 bg-white border border-red-500 hover:bg-red-600 text-red-500 hover:text-white font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
