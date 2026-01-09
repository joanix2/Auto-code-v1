import React from "react";
import { Link, useLocation } from "react-router-dom";
import { FolderGit2, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Repositories", href: "/repositories", icon: FolderGit2 },
  { name: "Issues", href: "/issues", icon: FileText },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="hidden md:flex md:flex-shrink-0">
      <div className="flex flex-col w-64 border-r bg-gray-50">
        <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
          <nav className="mt-5 flex-1 px-2 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    isActive ? "bg-primary text-white" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                    "group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors"
                  )}
                >
                  <item.icon className={cn(isActive ? "text-white" : "text-gray-400 group-hover:text-gray-500", "mr-3 flex-shrink-0 h-6 w-6")} aria-hidden="true" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </aside>
  );
}
