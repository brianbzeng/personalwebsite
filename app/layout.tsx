import type { Metadata } from "next";
import "./globals.css";
import LandscapeGuard from './components/LandscapeGuard';

export const metadata: Metadata = {
  title: "Brian Zeng / Project Archive",
  description: "A three-dimensional project archive of data, software, and applied AI work by Brian Zeng.",
  metadataBase: new URL("https://brianbzeng.com"),
  openGraph: {
    title: "Brian Zeng / Project Archive",
    description: "A three-dimensional project archive of data, software, and applied AI projects.",
    type: "website",
    images: [{ url: "/og.png", width: 1733, height: 908, alt: "Brian Zeng Neon Cabinet portfolio" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Brian Zeng / Neon Cabinet",
    description: "An interactive portfolio of data, software, and applied AI projects.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><LandscapeGuard>{children}</LandscapeGuard></body>
    </html>
  );
}
