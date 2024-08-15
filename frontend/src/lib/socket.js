import { io } from "socket.io-client";

const socket = io({
  path: "/api/socket.io",
  autoConnect: true,
});

export default socket;
