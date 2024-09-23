"use client";

import { useEffect } from "react";
import { createContext, useContext, useReducer } from "react";
import { api } from "@/lib";
import { getCookie } from "@/lib/cookies";

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
        `Unknown action: ${action.type}. Remember action type must be CAPITAL text.`
      );
  }
};

const AuthContextProvider = ({ children }) => {
  const [auth, dispatch] = useReducer(authReducer, initialAuthState);

  useEffect(() => {
    const updateToken = async () => {
      const token = await getCookie("AUTH_TOKEN");
      if (token) {
        api.setToken(token);
        dispatch({
          type: "UPDATE",
          payload: { token, isLogin: true },
        });
      }
    };
    updateToken();
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
