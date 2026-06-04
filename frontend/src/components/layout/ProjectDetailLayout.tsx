import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, useLocation, Link } from "react-router-dom";
import { ArrowLeft, Ticket, Network, Layers, GitBranch, BarChart3, User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { useProjects } from "@/hooks/useProjects";

interface ProjectDetailLayoutProps {
  children: React.ReactNode;
  projectId: string;
  user?: { username: string; avatar_url?: string; profile_picture?: string };
  onSignOut?: () => void;
}

const tabs = [
  { value: "tickets", label: "Tickets", icon: Ticket },
  { value: "ontologie", label: "Ontologie", icon: Network },
  { value: "architecture", label: "Architecture", icon: Layers },
  { value: "deploiement", label: "Déploiement", icon: GitBranch },
  { value: "monitoring", label: "Monitoring", icon: BarChart3 },
];

export function ProjectDetailLayout({ children, projectId, user, onSignOut }: ProjectDetailLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [projectName, setProjectName] = useState<string>("");
  const { getProject } = useProjects();
  const activeTab = searchParams.get("tab") || "tickets";

  useEffect(() => {
    const stateName = (location.state as { projectName?: string } | null)?.projectName;
    if (stateName) {
      setProjectName(stateName);
    } else if (projectId) {
      getProject(projectId)
        .then((p) => setProjectName(p.name))
        .catch(() => {});
    }
  }, [projectId, location.state, getProject]);

  const setActiveTab = (value: string) => {
    setSearchParams({ tab: value }, { replace: true });
  };

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
      <header className="border-b bg-white shadow-sm flex-shrink-0">
        <div className="px-3 md:px-4 py-2">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => navigate("/development/projets")} title="Retour aux projets">
              <ArrowLeft className="h-5 w-5" />
            </Button>

            <span className="font-semibold text-sm md:text-base truncate max-w-[120px] md:max-w-[200px]">{projectName}</span>

            <div className="flex-1" />

            <nav className="hidden md:flex items-center justify-center gap-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.value;
                return (
                  <button
                    key={tab.value}
                    onClick={() => setActiveTab(tab.value)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors whitespace-nowrap",
                      isActive ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>

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

      <main className="flex-1 overflow-y-auto bg-gray-50">{children}</main>

      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-50">
        <div className="flex items-center justify-around">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.value;
            return (
              <button
                key={tab.value}
                onClick={() => setActiveTab(tab.value)}
                className={cn(
                  "flex flex-col items-center gap-0.5 py-2 px-3 text-xs font-medium transition-colors",
                  isActive ? "text-primary" : "text-gray-500 hover:text-gray-700"
                )}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
