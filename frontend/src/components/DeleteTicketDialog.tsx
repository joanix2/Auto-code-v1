import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Ticket } from "@/types";

interface DeleteTicketDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  ticket: Ticket | null;
  onConfirm: () => void;
  loading?: boolean;
}

export function DeleteTicketDialog({ open, onOpenChange, ticket, onConfirm, loading = false }: DeleteTicketDialogProps) {
  if (!ticket) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            Supprimer le ticket
          </DialogTitle>
          <DialogDescription className="pt-2">Êtes-vous sûr de vouloir supprimer ce ticket ? Cette action est irréversible.</DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 border border-slate-200 dark:border-slate-800">
            <h4 className="font-semibold text-slate-900 dark:text-white mb-2">{ticket.title}</h4>
            {ticket.description && <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{ticket.description}</p>}
            <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
              <span className="px-2 py-1 rounded bg-slate-200 dark:bg-slate-800">{ticket.status}</span>
              <span className="px-2 py-1 rounded bg-slate-200 dark:bg-slate-800">{ticket.priority}</span>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading} className="flex-1">
            Annuler
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirm} disabled={loading} className="flex-1">
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Suppression...
              </>
            ) : (
              "Supprimer"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
