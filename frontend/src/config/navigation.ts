import { FolderGit2, FileText, Home, Code, Database, Boxes, Users, Lightbulb, Wrench, UserCircle, Map, FileCode, FolderTree, FolderKanban, LucideIcon } from "lucide-react";

export interface NavigationItem {
  name: string;
  href?: string;
  icon: LucideIcon;
  children?: NavigationItem[];
}

export const navigation: NavigationItem[] = [
  { name: "Home", href: "/", icon: Home },
  {
    name: "Analyse",
    icon: Lightbulb,
    children: [
      { name: "Avatars client", href: "/analyse/avatars", icon: UserCircle },
      { name: "Besoins", href: "/analyse/besoins", icon: FileText },
      { name: "Solutions techniques", href: "/analyse/solutions", icon: Wrench },
      { name: "Clients", href: "/analyse/clients", icon: Users },
      { name: "Cartographie", href: "/analyse/cartographie", icon: Map },
    ],
  },
  {
    name: "Development",
    icon: Code,
    children: [
      { name: "Projets", href: "/development/projets", icon: FolderKanban },
      { name: "DSLs", href: "/development/dsls", icon: Database },
      { name: "Repositories", href: "/development/repositories", icon: FolderTree },
      { name: "Templates", href: "/development/templates", icon: FileCode },
    ],
  },
];
