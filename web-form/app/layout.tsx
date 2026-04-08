import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TechCorp Support — AI-Powered 24/7 Customer Service",
  description: "Get instant help from our AI-powered support team. Available 24/7 across Email, WhatsApp, and Web. Average response time: under 5 minutes.",
  keywords: ["TechCorp", "customer support", "AI assistant", "24/7 support", "help desk"],
  authors: [{ name: "TechCorp Solutions Inc." }],
  openGraph: {
    title: "TechCorp Support — AI-Powered 24/7 Customer Service",
    description: "Get instant help from our AI-powered support team. Available 24/7.",
    type: "website",
    locale: "en_US",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-[#030712] text-gray-100">{children}</body>
    </html>
  );
}
