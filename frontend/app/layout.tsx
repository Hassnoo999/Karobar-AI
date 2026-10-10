import type { Metadata } from "next";
import { SupabaseProvider } from "@/components/SupabaseProvider";
import { PublicNavigationProvider } from "@/components/PublicNavigation";
import "./globals.css";

export const metadata: Metadata = {
  title: "Karobaar AI | Every shop has a story. Now it has proof.",
  description: "Voice-first financial evidence for Pakistani merchants.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body className="font-sans">
        <SupabaseProvider><PublicNavigationProvider>{children}</PublicNavigationProvider></SupabaseProvider>
      </body>
    </html>
  );
}
