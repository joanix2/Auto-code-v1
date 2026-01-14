import React from "react";
import { NavigationMenu } from "./NavigationMenu";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

interface SidebarProps {
  mobileMenuOpen?: boolean;
  onMobileMenuChange?: (open: boolean) => void;
}

export function Sidebar({ mobileMenuOpen = false, onMobileMenuChange }: SidebarProps) {
  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64 border-r bg-gray-50">
          <div className="flex-1 flex flex-col overflow-y-auto">
            <NavigationMenu className="flex-1 px-2 pt-6 space-y-1" />
          </div>
        </div>
      </aside>

      {/* Mobile Drawer */}
      <Sheet open={mobileMenuOpen} onOpenChange={onMobileMenuChange}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetHeader className="border-b p-4">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <NavigationMenu onNavigate={() => onMobileMenuChange?.(false)} className="flex-1 px-2 py-4 space-y-1" />
        </SheetContent>
      </Sheet>
    </>
  );
}
