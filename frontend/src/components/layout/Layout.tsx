import React, { useState } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Toaster } from "@/components/ui/toaster";

interface LayoutProps {
  children: React.ReactNode;
  user?: {
    username: string;
    avatar_url?: string;
    profile_picture?: string;
  };
  onSignOut?: () => void;
}

export function Layout({ children, user, onSignOut }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Header - Toute la largeur */}
      <Header user={user} onSignOut={onSignOut} onMenuClick={() => setMobileMenuOpen(true)} />

      <div className="flex h-screen-minus-header overflow-hidden">
        {/* Sidebar (Desktop + Mobile Drawer) */}
        <Sidebar mobileMenuOpen={mobileMenuOpen} onMobileMenuChange={setMobileMenuOpen} />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gray-50">{children}</main>
      </div>

      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}
