import React from "react";
import { Link } from "react-router-dom";
import { User, LogOut } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
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
      <div className="px-3 sm:px-6 py-3">
        <div className="flex items-center justify-between gap-2 sm:gap-4">
          {/* Logo + Title */}
          <Link to="/repositories" className="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition-opacity group">
            <img src="/assets/logo_ticket_code.svg" alt="AutoCode Logo" className="h-8 w-8 sm:h-10 sm:w-10 transition-transform group-hover:scale-105" />
            <h1 className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">AutoCode</h1>
          </Link>

          {/* User Menu */}
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={getProfilePictureUrl()} alt={user.username} />
                    <AvatarFallback>{getInitials(user.username)}</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="flex items-center justify-start gap-2 p-2">
                  <div className="flex flex-col space-y-1 leading-none">
                    <p className="font-medium">{user.username}</p>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/profile" className="flex items-center cursor-pointer">
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onSignOut} className="cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
}
