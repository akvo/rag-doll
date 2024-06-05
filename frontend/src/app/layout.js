import "./globals.css";
import { Inter } from "next/font/google";
import { AuthContextProvider } from "@/context";
import { Header } from "@/components";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Agriconnect",
  description: "Lorem ipsum sit dolor...",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full bg-white">
      <AuthContextProvider>
        <body className={`${inter.className} min-h-full`}>
          <Header />
          <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <footer>&nbsp;</footer>
        </body>
      </AuthContextProvider>
    </html>
  );
}
