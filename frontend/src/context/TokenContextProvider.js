"use client";
import { createContext, useContext, useState } from "react";

const TokenContext = createContext();

const TokenContextProvider = ({ children }) => {
  const [token, setToken] = useState(null);

  return (
    <TokenContext.Provider value={{ token, setToken }}>
      {children}
    </TokenContext.Provider>
  );
};

export const useToken = () => useContext(TokenContext);

export default TokenContextProvider;
