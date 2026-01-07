import React from "react";
import { Link } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  user?: {
    username: string;
    avatar_url?: string;
    profile_picture?: string;
  };
  onSignOut?: () => void;
}

export function Header({ user, onSignOut }: HeaderProps) {
  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase();
  };

  const getProfilePictureUrl = () => {
    if (user?.avatar_url) {
      return user.avatar_url;
    }
    if (user?.profile_picture) {
      if (user.profile_picture.startsWith("http://") || user.profile_picture.startsWith("https://")) {
        return user.profile_picture;
      }
      return `/assets/${user.profile_picture}?t=${Date.now()}`;
    }
    return undefined;
  };

  return (
    <header className="border-b bg-white shadow-sm z-10">
      <div className="p-3 sm:p-6 py-3">
        <div className="flex items-center justify-between gap-2 sm:gap-4">
          {/* Logo + Title */}
          <Link to="/repositories" className="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition-opacity group">
            <img src="/logo_ticket_code.svg" alt="AutoCode Logo" className="h-8 w-8 sm:h-10 sm:w-10 transition-transform group-hover:scale-105" />
            <h1 className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">AutoCode</h1>
          </Link>

          {/* User Menu */}
          {user && (
            <Link to="/profile">
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={getProfilePictureUrl()} alt={user.username} />
                  <AvatarFallback>{getInitials(user.username)}</AvatarFallback>
                </Avatar>
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
