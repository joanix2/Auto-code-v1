import { Button } from "@/components/ui/button";
import { TicketStatus } from "@/types";

interface Ticket {
  id: string;
  title: string;
  status: TicketStatus;
  order: number;
}

interface DevelopmentBannerProps {
  tickets: Ticket[];
  developing: boolean;
  onDevelop: (ticketId: string) => void;
}

export function DevelopmentBanner({ tickets, developing, onDevelop }: DevelopmentBannerProps) {
  if (tickets.length === 0) return null;

  const openTickets = tickets.filter((t) => t.status === TicketStatus.OPEN);
  if (openTickets.length === 0) return null;

  const nextTicket = openTickets.sort((a, b) => a.order - b.order)[0];

  return (
    <div className="relative overflow-hidden bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm hover:shadow-md transition-shadow">
      {/* Gradient accent bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-500 via-teal-500 to-cyan-500"></div>

      <div className="p-5 space-y-3">
        {/* Ligne 1: Nombre de tickets ouverts */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600 dark:text-slate-400">Tickets dans la queue</span>
          <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm font-semibold">
            {openTickets.length} ouvert{openTickets.length > 1 ? "s" : ""}
          </span>
        </div>

        {/* Ligne 2: Prochain ticket */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600 dark:text-slate-400">Prochain ticket</span>
          <span className="text-sm font-semibold text-slate-900 dark:text-white truncate ml-4">{nextTicket.title}</span>
        </div>

        {/* Ligne 3: Bouton pleine largeur */}
        <Button
          onClick={() => onDevelop(nextTicket.id)}
          disabled={developing}
          size="lg"
          className="w-full bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {developing ? (
            <>
              <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Développement en cours...
            </>
          ) : (
            <>
              <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              Développer automatiquement
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
