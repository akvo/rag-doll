"use client";

import { io } from "socket.io-client";

let socket;

if (typeof window !== "undefined") {
  const { hostname, origin } = window.location;
  const isLocalhost = hostname === "localhost";

  const transports = isLocalhost
    ? ["polling", "websocket"]
    : ["websocket", "polling"];

  socket = io(origin, {
    path: "/api/socket.io",
    transports: transports,
    reconnection: true,
    reconnectionAttempts: 20,
    reconnectionDelay: 5000,
    pingInterval: 65000, // 65 seconds
    pingTimeout: 60000, // 60 seconds
    upgrade: isLocalhost ? false : true,
  });
}

export default socket;
