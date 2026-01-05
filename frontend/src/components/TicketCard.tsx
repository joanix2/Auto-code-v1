import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Ticket } from "@/types";

interface TicketCardProps {
  ticket: Ticket;
  onEdit?: (ticketId: string) => void;
  onDelete?: (ticketId: string) => void;
}

export function TicketCard({ ticket, onEdit, onDelete }: TicketCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "in_progress":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "pending_validation":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200";
      case "closed":
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
      case "cancelled":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "text-red-600 dark:text-red-400";
      case "high":
        return "text-orange-600 dark:text-orange-400";
      case "medium":
        return "text-yellow-600 dark:text-yellow-400";
      case "low":
        return "text-green-600 dark:text-green-400";
      default:
        return "text-slate-600 dark:text-slate-400";
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "feature":
        return "Fonctionnalité";
      case "bugfix":
        return "Correction de bug";
      case "refactor":
        return "Refactorisation";
      case "documentation":
        return "Documentation";
      default:
        return type;
    }
  };

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case "critical":
        return "Critique";
      case "high":
        return "Haute";
      case "medium":
        return "Moyenne";
      case "low":
        return "Basse";
      default:
        return priority;
    }
  };

  return (
    <Card className="group hover:shadow-lg transition-all duration-300 border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
      <CardContent className="p-0">
        {/* Header avec statut */}
        <div className="px-6 pt-5 pb-4">
          <div className="flex items-start justify-between gap-3 mb-3">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex-1 line-clamp-2">{ticket.title}</h3>
            <span className={`px-3 py-1 rounded-md text-xs font-medium whitespace-nowrap ${getStatusColor(ticket.status)}`}>{ticket.status.replace("_", " ")}</span>
          </div>

          {ticket.description && <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-3 mb-4">{ticket.description}</p>}

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <svg className={`h-4 w-4 ${getPriorityColor(ticket.priority)}`} fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1zm-5 8.274l-.818 2.552c-.25.78.03 1.632.753 2.03.447.25.998.245 1.413-.01.428-.266.713-.743.713-1.26a3 3 0 00-2.06-2.312z" />
              </svg>
              <span className={`font-medium ${getPriorityColor(ticket.priority)}`}>{getPriorityLabel(ticket.priority)}</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-500">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                />
              </svg>
              <span>{getTypeLabel(ticket.ticket_type)}</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-500">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>{formatDate(ticket.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Footer avec boutons */}
        <div className="border-t border-slate-100 dark:border-slate-800 px-6 py-3 bg-slate-50/50 dark:bg-slate-800/50 flex items-center gap-2">
          <Link to={`/ticket/${ticket.id}/chat`} className="flex-1">
            <Button variant="ghost" size="sm" className="w-full hover:bg-blue-50 dark:hover:bg-blue-950/50 text-blue-600 dark:text-blue-400">
              <svg className="h-4 w-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              Chat
            </Button>
          </Link>
          {onDelete && (
            <Button variant="ghost" size="sm" onClick={() => onDelete(ticket.id)} className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/50">
              <svg className="h-4 w-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Supprimer
            </Button>
          )}
          {onEdit && (
            <Button variant="ghost" size="sm" onClick={() => onEdit(ticket.id)} className="flex-1 hover:bg-slate-100 dark:hover:bg-slate-800">
              <svg className="h-4 w-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              Éditer
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
