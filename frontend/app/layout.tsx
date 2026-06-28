import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ghost-sweep",
  description: "Job Integrity Database for evidence-based hiring transparency",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
