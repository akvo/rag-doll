import "./globals.css";
import { Inter } from "next/font/google";
import { AuthContextProvider } from "@/context";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Agriconnect",
  description: "Lorem ipsum sit dolor...",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <AuthContextProvider>
        <body className={inter.className}>
          <header>&nbsp;</header>
          {children}
          <footer>&nbsp;</footer>
        </body>
      </AuthContextProvider>
    </html>
  );
}
