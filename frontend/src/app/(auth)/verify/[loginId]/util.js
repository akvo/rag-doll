"use server";

import { cookies } from "next/headers";

export const setCookie = (name, value) => {
  cookies().set(name, value);
};
