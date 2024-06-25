"use client";
import { createContext, useContext, useReducer } from "react";

const UserContext = createContext(null);
const UserDispatchContext = createContext(null);

const initalUserState = {
  id: null,
  name: "",
  email: "",
};

const userReducer = (state, action) => {
  switch (action.type) {
    case "UPDATE":
      return {
        ...state,
        id: action.payload.id,
        name: action.payload.name,
        email: action.payload.email,
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
