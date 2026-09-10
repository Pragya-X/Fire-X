import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { ToastProvider } from "@/components/ui/primitives";

export const metadata: Metadata = {
  title: "FIRE-X | Fire Intelligence & Risk Evaluation Platform",
  description: "AI-enabled geospatial fire intelligence platform. Detect. Classify. Understand. Respond.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}