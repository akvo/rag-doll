"use client";
import { createContext, useContext, useReducer } from "react";

const AuthContext = createContext(null);
const AuthDispatchContext = createContext(null);

const authReducer = (state, action) => {
  switch (action.type) {
    case "UPDATE":
      return {
        ...state,
        token: action.payload.token,
        isLogin: action.payload.isLogin,
      };
    default:
      throw Error(`Unknown action: ${action.type}`);
  }
};

const AuthContextProvider = ({ children }) => {
  const [auth, dispatch] = useReducer(authReducer, {
    token: null,
    isLogin: false,
  });

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
