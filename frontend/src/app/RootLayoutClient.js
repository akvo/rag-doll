"use client";

import { AuthContextProvider } from "@/context";
import { roboto_condensed } from "./fonts";

export default function RootLayoutClient({ children }) {
  return (
    <AuthContextProvider>
      <style jsx global>{`
        h1,
        h2,
        h3,
        h4,
        h5,
        h6 {
          font-family: ${roboto_condensed.style.fontFamily};
        }
      `}</style>
      <main>{children}</main>
    </AuthContextProvider>
  );
}
