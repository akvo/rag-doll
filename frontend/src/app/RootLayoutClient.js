"use client";

import { useEffect } from "react";
import { AuthContextProvider } from "@/context";
import { roboto_condensed } from "./fonts";

export default function RootLayoutClient({ children }) {
  // register service worker
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then(function (reg) {
          console.log("Service Worker registered with scope:", reg.scope);
        })
        .catch(function (err) {
          console.log("Service Worker registration failed:", err);
        });
    }
  }, []);

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
