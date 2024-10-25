"use client";

import { useEffect } from "react";
import { api } from "@/lib";

const urlBase64ToUint8Array = (base64String) => {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
};

const PushNotifications = () => {
  useEffect(() => {
    const subscribeUser = async (registration) => {
      try {
        const vapidPublicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
        if (!vapidPublicKey) {
          throw new Error("VAPID public key is missing.");
        }

        const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: applicationServerKey,
        });

        // Send subscription details to the backend
        const response = await api.post(
          "subscribe",
          JSON.stringify(subscription)
        );

        if (response.ok) {
          console.info("User subscribed successfully!");
        } else {
          console.error(
            "Failed to subscribe the user. Full response:",
            response
          );
        }
      } catch (error) {
        console.error("Error during subscription:", error);
      }
    };

    const handleNotificationPermission = async () => {
      if (Notification.permission === "granted") {
        const registration = await navigator.serviceWorker.ready;
        subscribeUser(registration);
      } else if (Notification.permission === "default") {
        const permission = await Notification.requestPermission();
        if (permission === "granted") {
          const registration = await navigator.serviceWorker.ready;
          subscribeUser(registration);
        } else {
          console.warn("Notification permission was denied.");
        }
      } else {
        console.warn(
          "Notifications are blocked. Enable them in your browser settings if you want to receive notifications."
        );
      }
    };

    if ("Notification" in window && "serviceWorker" in navigator) {
      handleNotificationPermission();
    } else {
      console.warn("Push notifications are not supported in this browser.");
    }
  }, []);

  return null;
};

export default PushNotifications;
