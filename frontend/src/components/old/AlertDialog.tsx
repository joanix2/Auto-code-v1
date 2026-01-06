import { Dialog, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogPortal, DialogOverlay } from "@/components/ui/dialog";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";
import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import * as React from "react";

export type AlertVariant = "success" | "error" | "warning" | "info";

interface AlertDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  variant?: AlertVariant;
  icon?: LucideIcon;
  children?: ReactNode;
  closeLabel?: string;
  onClose?: () => void;
}

const variantStyles = {
  success: {
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
  },
  error: {
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
  },
  warning: {
    iconBg: "bg-yellow-100",
    iconColor: "text-yellow-600",
  },
  info: {
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
  },
};

// DialogContent personnalisé sans le bouton X de fermeture
const DialogContentWithoutClose = React.forwardRef<React.ElementRef<typeof DialogPrimitive.Content>, React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>>(
  ({ className, children, ...props }, ref) => (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        ref={ref}
        className={cn(
          "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-3 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
          className
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Content>
    </DialogPortal>
  )
);
DialogContentWithoutClose.displayName = "DialogContentWithoutClose";

export function AlertDialog({ open, onOpenChange, title, description, variant = "info", icon: Icon, children, closeLabel = "Fermer", onClose }: AlertDialogProps) {
  const styles = variantStyles[variant];

  const handleClose = () => {
    onOpenChange(false);
    onClose?.();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContentWithoutClose className="sm:max-w-[500px]">
        <DialogHeader>
          {Icon && (
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 ${styles.iconBg} rounded-full`}>
                <Icon className={`h-6 w-6 ${styles.iconColor}`} />
              </div>
              <DialogTitle className="text-xl">{title}</DialogTitle>
            </div>
          )}
          {!Icon && <DialogTitle className="text-xl">{title}</DialogTitle>}

          {description && <DialogDescription className="text-base pt-2">{description}</DialogDescription>}
        </DialogHeader>

        {children && <div className="pt-2">{children}</div>}

        <DialogFooter>
          <Button onClick={handleClose} className="w-full sm:w-auto">
            {closeLabel}
          </Button>
        </DialogFooter>
      </DialogContentWithoutClose>
    </Dialog>
  );
}
