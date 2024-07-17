import "./globals.css";
import { Inter } from "next/font/google";
import { AuthContextProvider } from "@/context";
// import { Header } from "@/components";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Agriconnect",
  description: "Lorem ipsum sit dolor...",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full bg-white">
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <body className={`${inter.className} min-h-full`}>
        <AuthContextProvider>
          {/* <Header /> */}
          <main>{children}</main>
          {/* <footer>&nbsp;</footer> */}
        </AuthContextProvider>
      </body>
    </html>
  );
}
