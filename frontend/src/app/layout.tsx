import type { Metadata } from "next";

import "./globals.css";

import { AuthProvider } from "@/providers/AuthProvider";

export const metadata: Metadata = {
  title: "Profit Radar",
  description: "AI Sales OS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ja"
      className="h-full antialiased"
    >
      <body className="min-h-screen bg-slate-50">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
