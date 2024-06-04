"use client";
import { createContext, useContext, useReducer } from "react";

const AuthContext = createContext(null);
const AuthDispatchContext = createContext(null);

const authReducer = (state, action) => {
  switch (action.type) {
    case "UPDATE":
      return {
        token: action.payload.token,
      };
    default:
      throw Error(`Unknown action: ${action.type}`);
  }
};

const AuthContextProvider = ({ children }) => {
  const [auth, dispatch] = useReducer(authReducer, { token: null });

  return (
    <AuthContext.Provider value={auth}>
      <AuthDispatchContext.Provider value={dispatch}>
        {children}
      </AuthDispatchContext.Provider>
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => useContext(AuthContext);

export const useAuthDispatch = () => useContext(AuthDispatchContext);

export default AuthContextProvider;
