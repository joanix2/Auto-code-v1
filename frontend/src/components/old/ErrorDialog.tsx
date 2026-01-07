import { AlertDialog } from "@/components/DeleteDialog";
import { XCircle } from "lucide-react";

interface ErrorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  error: string | Error;
  details?: string;
}

export function ErrorDialog({ open, onOpenChange, title = "Une erreur est survenue", error, details }: ErrorDialogProps) {
  const errorMessage = typeof error === "string" ? error : error.message;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange} title={title} variant="error" icon={XCircle} closeLabel="Fermer">
      <div className="space-y-3">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800 font-medium">{errorMessage}</p>
        </div>

        {details && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-xs text-gray-600 font-mono break-all">{details}</p>
          </div>
        )}

        <p className="text-xs text-gray-500">Si le problème persiste, veuillez contacter le support.</p>
      </div>
    </AlertDialog>
  );
}
