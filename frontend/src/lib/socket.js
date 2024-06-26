import { io } from "socket.io-client";

const socket = io({
  // transports: ["websocket", "polling"],
  path: "/api/socket.io",
  autoConnect: false,
});

export default socket;
