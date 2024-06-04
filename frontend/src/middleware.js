import { NextResponse } from "next/server";

const protectedRoutes = ["/", "/settings", "/chats"];
const authRoutes = ["/login"];
// const publicRoutes = ["/register", "/verify"];

export const middleware = (request) => {
  const authToken = request.cookies.get("AUTH_TOKEN")?.value;

  if (
    protectedRoutes.includes(request.nextUrl.pathname) &&
    (!authToken || Date.now() > JSON.parse(authToken).expiredAt)
  ) {
    request.cookies.delete("AUTH_TOKEN");
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete("AUTH_TOKEN");
    return response;
  }

  if (authRoutes.includes(request.nextUrl.pathname) && authToken) {
    return NextResponse.redirect(new URL("/", request.url));
  }
};
