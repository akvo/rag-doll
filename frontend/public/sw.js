// Force immediate activation of the updated Service Worker
self.addEventListener("install", (event) => {
  self.skipWaiting(); // Activate new service worker immediately
});

self.addEventListener("activate", (event) => {
  event.waitUntil(clients.claim()); // Take control of all clients
});

// Handle push events
self.addEventListener("push", function (event) {
  const data = event.data.json();
  const title = data.title;
  const options = {
    body: data.body,
    // icon: "/images/whisper-logo.png",
    // data: {
    //   url: data.url || "/",
    // },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// Handle notification click events
self.addEventListener("notificationclick", function (event) {
  event.notification.close(); // Close the notification after click

  // Retrieve the URL from the notification's data, with a fallback if missing
  const targetUrl = event?.currentTarget?.registration?.scope;
  if (!targetUrl) {
    console.error("No target URL");
    return;
  }

  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clientList) => {
        // Check if the URL is already open in any client
        for (const client of clientList) {
          if (client.url === targetUrl && "focus" in client) {
            return client.focus(); // Focus the tab if already open
          }
        }
        // Open a new tab if the URL is not open
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});
