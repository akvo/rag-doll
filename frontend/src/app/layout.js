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
    <html lang="en" className="h-full bg-white">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>{metadata.title}</title>
        <meta name="description" content={metadata.description} />
        <link
          href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&family=Roboto+Condensed:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
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
