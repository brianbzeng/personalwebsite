import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Brian Zeng",
  description:
    "Data analyst and developer based in Oakland, California. Projects in sports analytics, machine learning, and applied AI.",
  metadataBase: new URL("https://brianbzeng.com"),
  openGraph: {
    title: "Brian Zeng",
    description: "Data analyst and developer based in Oakland, California.",
    type: "website",
    images: [
      {
        url: "/og.png",
        width: 1733,
        height: 908,
        alt: "Brian Zeng portfolio",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Brian Zeng",
    description: "Data analyst and developer based in Oakland, California.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const themeScript = `(function(){try{var saved=localStorage.getItem('bz-theme');var theme=saved==='light'||saved==='dark'?saved:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme}catch(e){}})();`;

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
