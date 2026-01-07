import React from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

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
  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header user={user} onSignOut={onSignOut} />

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto bg-gray-50">{children}</main>
        </div>
      </div>
    </div>
  );
}
