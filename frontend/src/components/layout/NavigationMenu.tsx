import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { navigation } from "@/config/navigation";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

interface NavigationMenuProps {
  onNavigate?: () => void;
  className?: string;
}

export function NavigationMenu({ onNavigate, className }: NavigationMenuProps) {
  const location = useLocation();

  return (
    <nav className={cn("overflow-y-auto overflow-x-hidden", className)}>
      {navigation.map((item) => {
        // Item avec sous-menu (Accordion)
        if (item.children && item.children.length > 0) {
          const hasActiveChild = item.children.some((child) => child.href && location.pathname === child.href);

          return (
            <Accordion key={item.name} type="single" collapsible className="w-full">
              <AccordionItem value={item.name} className="border-none">
                <AccordionTrigger
                  className={cn(
                    "group flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors hover:no-underline",
                    hasActiveChild ? "bg-primary/10 text-primary" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                  )}
                >
                  <div className="flex items-center flex-1">
                    <item.icon className={cn(hasActiveChild ? "text-primary" : "text-gray-400 group-hover:text-gray-500", "mr-3 flex-shrink-0 h-5 w-5")} aria-hidden="true" />
                    {item.name}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-1 pt-1">
                  <div className="space-y-1 ml-8">
                    {item.children.map((child) => {
                      const isChildActive = child.href && location.pathname === child.href;
                      return (
                        <Link
                          key={child.name}
                          to={child.href || "#"}
                          onClick={onNavigate}
                          className={cn(
                            isChildActive ? "bg-primary text-white" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                            "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                          )}
                        >
                          <child.icon className={cn(isChildActive ? "text-white" : "text-gray-400 group-hover:text-gray-500", "mr-3 flex-shrink-0 h-4 w-4")} aria-hidden="true" />
                          {child.name}
                        </Link>
                      );
                    })}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          );
        }

        // Item simple (Bouton/Link)
        const isActive = item.href && location.pathname === item.href;
        return (
          <Link
            key={item.name}
            to={item.href || "#"}
            onClick={onNavigate}
            className={cn(
              isActive ? "bg-primary text-white" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              "group flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors",
            )}
          >
            <item.icon className={cn(isActive ? "text-white" : "text-gray-400 group-hover:text-gray-500", "mr-3 flex-shrink-0 h-5 w-5")} aria-hidden="true" />
            {item.name}
          </Link>
        );
      })}
    </nav>
  );
}
