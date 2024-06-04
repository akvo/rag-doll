import { Inter } from "next/font/google";
import "./globals.css";
import { TokenContextProvider } from "@/context";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Agriconnect",
  description: "Lorem ipsum sit dolor...",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <TokenContextProvider>
        <body className={inter.className}>
          <header>&nbsp;</header>
          {children}
          <footer>&nbsp;</footer>
        </body>
      </TokenContextProvider>
    </html>
  );
}
