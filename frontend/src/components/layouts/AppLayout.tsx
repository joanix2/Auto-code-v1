import React from "react";
import { Link } from "react-router-dom";
import { User, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { user, signOut } = useAuth();

  // Get initials from username
  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase();
  };

  // Get profile picture URL
  const getProfilePictureUrl = () => {
    if (user?.avatar_url) {
      // If it's already a full URL (from GitHub), use it directly
      if (user.avatar_url.startsWith("http://") || user.avatar_url.startsWith("https://")) {
        return user.avatar_url;
      }
      // Otherwise, it's a local asset - construct the URL
      return `/assets/${user.avatar_url}?t=${Date.now()}`;
    }
    return undefined;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Navigation Bar */}
          <header className="border-b bg-white shadow-sm z-10">
            <div className="p-3 sm:p-6 py-3">
              <div className="flex items-center justify-between gap-2 sm:gap-4">
                {/* Logo + Title */}
                <Link to="/projects" className="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition-opacity group">
                  <img src="/assets/logo_ticket_code.svg" alt="AutoCode Logo" className="h-8 w-8 sm:h-10 sm:w-10 transition-transform group-hover:scale-105" />
                  <h1 className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">AutoCode</h1>
                </Link>

                {/* User Menu */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-9 w-9 sm:h-10 sm:w-10 rounded-full ring-2 ring-transparent hover:ring-primary/20 transition-all">
                      <Avatar className="h-9 w-9 sm:h-10 sm:w-10">
                        <AvatarImage src={getProfilePictureUrl()} alt={user?.username} />
                        <AvatarFallback className="bg-gradient-to-br from-primary to-purple-600 text-white">{user?.username ? getInitials(user.username) : "U"}</AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56" align="end">
                    {user && (
                      <>
                        <div className="flex flex-col space-y-1 p-2">
                          <p className="text-sm font-medium">{user.username}</p>
                          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                        </div>
                        <DropdownMenuSeparator />
                      </>
                    )}
                    <DropdownMenuItem asChild>
                      <Link to="/profile" className="cursor-pointer flex w-full items-center">
                        <User className="mr-2 h-4 w-4" />
                        <span>Profile</span>
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={signOut} className="cursor-pointer text-destructive focus:text-destructive">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Log out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <div className="flex-1 overflow-auto">{children}</div>
        </div>
      </div>
    </div>
  );
}
