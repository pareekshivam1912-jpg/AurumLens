import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ChatbotDock from "@/components/ChatbotDock";

export const metadata: Metadata = {
  title: "AurumLens — MCX Gold RV Intelligence",
  description: "Cross-contract relative-value and hedging-cost intelligence for MCX gold contracts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased flex h-screen overflow-hidden bg-[#FDFBF7]">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto p-6 bg-[#FDFBF7]">{children}</main>
          <Footer />
        </div>
        <ChatbotDock />
      </body>
    </html>
  );
}
