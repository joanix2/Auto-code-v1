import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Link } from "react-router-dom";

interface FullPageLayoutProps {
  children: React.ReactNode;
  title?: string;
  backUrl?: string;
  hideHeader?: boolean;
  user?: { username: string; avatar_url?: string; profile_picture?: string };
  onSignOut?: () => void;
}

export function FullPageLayout({ children, title, backUrl, hideHeader, user, onSignOut }: FullPageLayoutProps) {
  const navigate = useNavigate();

  const getInitials = (username: string) => username.slice(0, 2).toUpperCase();
  const getProfilePictureUrl = () => {
    if (user?.avatar_url) return user.avatar_url;
    if (user?.profile_picture) {
      if (user.profile_picture.startsWith("http://") || user.profile_picture.startsWith("https://")) return user.profile_picture;
      return `/assets/${user.profile_picture}?t=${Date.now()}`;
    }
    return undefined;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {!hideHeader && (
      <header className="border-b bg-white shadow-sm flex-shrink-0">
        <div className="px-3 md:px-4 py-2">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => navigate(backUrl || "/")} title="Retour">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            {title && <span className="font-semibold text-sm md:text-base truncate">{title}</span>}
            <div className="flex-1" />
            {user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-7 w-7 md:h-8 md:w-8">
                      <AvatarImage src={getProfilePictureUrl()} alt={user.username} />
                      <AvatarFallback>{getInitials(user.username)}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="flex items-center justify-start gap-2 p-2">
                    <p className="font-medium text-sm">{user.username}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/profile" className="flex items-center cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={onSignOut} className="cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </header>
      )}
      <main className="flex-1 flex flex-col bg-gray-50">
        <div className="flex-1 relative">{children}</div>
      </main>
    </div>
  );
}
