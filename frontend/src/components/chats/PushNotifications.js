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
          userVisibleOnly: true, // Essential for requiring explicit permission
          applicationServerKey: applicationServerKey, // Uint8Array VAPID key
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

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.info("Service Worker registered successfully.");
          subscribeUser(registration); // Subscribe the user after service worker registration
        })
        .catch((error) => {
          console.error("Service Worker registration failed:", error);
        });
    }
  }, []);

  return null;
};

export default PushNotifications;
