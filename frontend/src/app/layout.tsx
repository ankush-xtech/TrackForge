import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/layout/providers";

export const metadata: Metadata = {
  title: "WebWork - Employee Activity Tracking",
  description: "Track employee time, activity, and productivity with WebWork",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
