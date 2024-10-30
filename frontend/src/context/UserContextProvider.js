"use client";

import { useEffect } from "react";
import { createContext, useContext, useReducer } from "react";
import { api } from "@/lib";

const UserContext = createContext(null);
const UserDispatchContext = createContext(null);

const initalUserState = {
  id: null,
  name: "",
  phone_number: "",
  clients: [],
};

const userReducer = (state, action) => {
  switch (action.type) {
    case "UPDATE":
      return {
        ...state,
        id: action.payload.id,
        name: action.payload.name,
        phone_number: action.payload.phone_number,
        clients: action.payload.clients,
      };
    case "DELETE":
      return initalUserState;
    default:
      throw Error(
        `Unknown action: ${action.type}. Remeber action type must be CAPITAL text.`
      );
  }
};

const UserContextProvider = ({ children }) => {
  const [user, dispatch] = useReducer(userReducer, initalUserState);

  useEffect(() => {
    const fetchUserMe = async () => {
      const res = await api.get("me");
      if (res.status === 200) {
        const resData = await res.json();
        dispatch({ type: "UPDATE", payload: { ...resData } });
      }
    };
    fetchUserMe();
  }, []);

  return (
    <UserContext.Provider value={user}>
      <UserDispatchContext.Provider value={dispatch}>
        {children}
      </UserDispatchContext.Provider>
    </UserContext.Provider>
  );
};

export const useUserContext = () => useContext(UserContext);
export const useUserDispatch = () => useContext(UserDispatchContext);

export default UserContextProvider;
