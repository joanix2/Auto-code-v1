import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "@/components/ui/button";

export function AppBar() {
  const { user, signOut } = useAuth();

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
            <div className="text-sm text-slate-600 dark:text-slate-400 hidden sm:block">
              <span className="font-medium">{user.username}</span>
            </div>
          )}
          <Button onClick={signOut} variant="ghost" size="sm" className="text-slate-600 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </Button>
        </div>
      </div>
    </header>
  );
}
