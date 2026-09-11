import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { ToastProvider } from "@/components/ui/primitives";

export const metadata: Metadata = {
  title: "FIRE-X | Fire Intelligence & Risk Evaluation Platform",
  description: "AI-enabled geospatial fire intelligence platform. Detect. Classify. Understand. Respond.",
};

// Applies the persisted theme before first paint so there is no white flash.
const themeInitScript = `
(function(){try{var t=localStorage.getItem("firex-theme")||"dark";document.documentElement.classList.toggle("dark",t==="dark");}catch(e){}})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
