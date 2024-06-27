import { io } from "socket.io-client";

const socket = io({
  path: "/api/socket.io",
  autoConnect: false,
});

export default socket;
