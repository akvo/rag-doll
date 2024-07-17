"use client";

import { useEffect } from "react";
import { createContext, useContext, useReducer } from "react";
import { getCookie } from "@/app/(auth)/verify/[loginId]/util";
import { api } from "@/lib";

const AuthContext = createContext(null);
const AuthDispatchContext = createContext(null);

const initialAuthState = {
  token: null,
  isLogin: false,
};

const authReducer = (state, action) => {
  switch (action.type) {
    case "UPDATE":
      return {
        ...state,
        token: action.payload.token,
        isLogin: action.payload.isLogin,
      };
    case "DELETE":
      return initialAuthState;
    default:
      throw Error(
        `Unknown action: ${action.type}. Remeber action type must be CAPITAL text.`
      );
  }
};

const AuthContextProvider = ({ children }) => {
  const [auth, dispatch] = useReducer(authReducer, initialAuthState);

  useEffect(() => {
    const setApiToken = async () => {
      const token = await getCookie("AUTH_TOKEN");
      if (token) {
        api.setToken(token);
      }
    };
    setApiToken();
  }, []);

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
