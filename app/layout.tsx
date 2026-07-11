import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Brian Zeng — Data Products & Software",
  description:
    "Brian Zeng builds useful data products for sports, markets, and messy decisions.",
  metadataBase: new URL("https://brianbzeng.com"),
  openGraph: {
    title: "Brian Zeng — Data Products & Software",
    description: "Tools for questions that don't have tidy answers.",
    type: "website",
    images: [
      {
        url: "/og.png",
        width: 1734,
        height: 907,
        alt: "Brian Zeng — Data Products and Software",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Brian Zeng — Data Products & Software",
    description: "Tools for questions that don't have tidy answers.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
