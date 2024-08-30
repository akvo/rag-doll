import { io } from "socket.io-client";

const socket = io({
  path: "/api/socket.io",
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 5000,
});

export default socket;
