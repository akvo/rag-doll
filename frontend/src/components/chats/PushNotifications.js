"use client";

import { useEffect, useCallback } from "react";

const PushNotifications = () => {
  // Function to handle subscription
  const subscribeUser = useCallback(async () => {
    // Ensure the service worker is ready
    const registration = await navigator.serviceWorker.ready;

    // Subscribe the user to push notifications
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(
        process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
      ), // Use your VAPID public key here
    });

    // Send subscription to your backend
    const response = await fetch("/api/subscribe", {
      method: "POST",
      body: JSON.stringify(subscription),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      console.log("User subscribed successfully");
    } else {
      console.error("Failed to subscribe the user");
    }
  }, []);

  // Utility to convert base64 VAPID key to Uint8Array
  const urlBase64ToUint8Array = (base64String) => {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  };

  // Call the subscribeUser function when the component mounts (or when the user takes action)
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      subscribeUser(); // Call to subscribe the user to push notifications
    }
  }, [subscribeUser]);

  return null;
};

export default PushNotifications;
