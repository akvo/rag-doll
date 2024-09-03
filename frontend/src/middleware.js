import { NextResponse } from "next/server";

const protectedRoutes = ["/account", "/chats"];
const authRoutes = ["/login"];

export const middleware = (request) => {
  const authToken = request.cookies.get("AUTH_TOKEN")?.value;

  // Redirect home to chats page if authenticated
  if (request.nextUrl.pathname === "/" && authToken) {
    return NextResponse.redirect(new URL("/chats", request.url));
  }

  // Redirect to login if trying to access a protected route without a token
  if (protectedRoutes.includes(request.nextUrl.pathname) && !authToken) {
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete("AUTH_TOKEN");
    return response;
  }

  // Redirect authenticated users away from the login page
  if (authRoutes.includes(request.nextUrl.pathname) && authToken) {
    return NextResponse.redirect(new URL("/chats", request.url));
  }

  // If none of the above conditions are met, continue with the request
  return NextResponse.next();
};
