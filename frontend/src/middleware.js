import { NextResponse } from "next/server";

const protectedRoutes = ["/", "/account", "/chats"];
const authRoutes = ["/login"];
// const publicRoutes = ["/register", "/verify"];

export const middleware = (request) => {
  const authToken = request.cookies.get("AUTH_TOKEN")?.value;

  // redirect home to chats page
  if (request.nextUrl.pathname === "/") {
    return NextResponse.redirect(new URL("/chats", request.url));
  }

  // redirect to login
  if (protectedRoutes.includes(request.nextUrl.pathname) && !authToken) {
    request.cookies.delete("AUTH_TOKEN");
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete("AUTH_TOKEN");
    return response;
  }

  // authenticated
  if (authRoutes.includes(request.nextUrl.pathname) && authToken) {
    return NextResponse.redirect(new URL("/chats", request.url));
  }
};
