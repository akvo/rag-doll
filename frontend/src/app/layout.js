import "./globals.css";
import RootLayoutClient from "./RootLayoutClient";
import { assistant } from "./fonts";

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
      </head>
      <body
        className={`${assistant.className} h-full min-h-screen bg-white overflow-hidden`}
      >
        <RootLayoutClient>{children}</RootLayoutClient>
      </body>
    </html>
  );
}
