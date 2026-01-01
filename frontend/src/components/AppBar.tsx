import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { User, LogOut, Settings } from "lucide-react";
import { API_URL } from "@/config/env";

export function AppBar() {
  const { user, signOut } = useAuth();

  // Get profile picture URL
  const getProfilePictureUrl = () => {
    if (user?.profile_picture) {
      const baseUrl = API_URL.replace(/\/api$/, "");
      return `${baseUrl}/assets/${user.profile_picture}?t=${Date.now()}`;
    }
    return undefined;
  };

  // Get initials from user's username
  const getInitials = (username: string) => {
    return username
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:border-slate-800 dark:bg-slate-950/95">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-8 max-w-7xl">
        <Link to="/projects" className="flex items-center gap-3 transition-opacity hover:opacity-80">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 shadow-md">
            <span className="text-xl">📦</span>
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent leading-tight">Auto-Code Platform</h1>
            <span className="text-xs text-slate-500 dark:text-slate-400">Gestion de projets</span>
          </div>
        </Link>
        <div className="flex items-center gap-3">
          {user && (
            <>
              <div className="text-sm text-slate-600 dark:text-slate-400 hidden sm:block">
                <span className="font-medium">{user.username}</span>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="relative h-8 w-8 rounded-full ring-2 ring-slate-200 dark:ring-slate-700 hover:ring-slate-300 dark:hover:ring-slate-600 transition-all cursor-pointer">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={getProfilePictureUrl()} alt={user.username} />
                      <AvatarFallback className="text-xs bg-gradient-to-br from-blue-500 to-violet-600 text-white">{getInitials(user.username)}</AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{user.username}</p>
                      <p className="text-xs leading-none text-muted-foreground">{user.email}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/profile" className="cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      <span>Profil</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/profile" className="cursor-pointer">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Paramètres</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={signOut} className="text-red-600 dark:text-red-400 cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Déconnexion</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
