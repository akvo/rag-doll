import { io } from "socket.io-client";

const socket = io({
  path: "/api/socket.io",
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 5000,
  pingInterval: 25000, // 25 seconds
  pingTimeout: 5000, // 5 seconds
});

export default socket;
