"use server";

import { cookies } from "next/headers";

export const setCookie = (name, value) => {
  cookies().set(name, value);
};

export const deleteCookie = (name) => {
  cookies().delete(name);
};

export const getCookie = (name) => {
  const cookie = cookies().get(name);
  return cookie ? cookie.value : null;
};
