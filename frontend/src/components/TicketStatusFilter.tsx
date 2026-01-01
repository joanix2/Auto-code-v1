import { TicketStatus } from "@/types";

interface TicketStatusFilterProps {
  selectedStatus: TicketStatus | "all";
  onStatusChange: (status: TicketStatus | "all") => void;
  statusCounts: Record<TicketStatus | "all", number>;
}

const STATUS_CONFIG = {
  all: { label: "Tous", color: "slate" },
  [TicketStatus.OPEN]: { label: "Ouvert", color: "blue" },
  [TicketStatus.IN_PROGRESS]: { label: "En cours", color: "yellow" },
  [TicketStatus.PENDING_VALIDATION]: { label: "En validation", color: "orange" },
  [TicketStatus.CLOSED]: { label: "Fermé", color: "green" },
  [TicketStatus.CANCELLED]: { label: "Annulé", color: "red" },
} as const;

export function TicketStatusFilter({ selectedStatus, onStatusChange, statusCounts }: TicketStatusFilterProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
      {Object.entries(STATUS_CONFIG).map(([status, config]) => {
        const isSelected = selectedStatus === status;
        const count = statusCounts[status as TicketStatus | "all"] || 0;
        const colorClass = getColorClass(config.color, isSelected);

        return (
          <button key={status} onClick={() => onStatusChange(status as TicketStatus | "all")} className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${colorClass}`}>
            {config.label}
            <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-white/20">{count}</span>
          </button>
        );
      })}
    </div>
  );
}

function getColorClass(color: string, isSelected: boolean): string {
  const baseClasses = "border";

  if (isSelected) {
    switch (color) {
      case "slate":
        return `${baseClasses} bg-slate-600 text-white border-slate-700`;
      case "blue":
        return `${baseClasses} bg-blue-600 text-white border-blue-700`;
      case "yellow":
        return `${baseClasses} bg-yellow-600 text-white border-yellow-700`;
      case "orange":
        return `${baseClasses} bg-orange-600 text-white border-orange-700`;
      case "green":
        return `${baseClasses} bg-green-600 text-white border-green-700`;
      case "red":
        return `${baseClasses} bg-red-600 text-white border-red-700`;
      default:
        return `${baseClasses} bg-slate-600 text-white border-slate-700`;
    }
  } else {
    switch (color) {
      case "slate":
        return `${baseClasses} bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700`;
      case "blue":
        return `${baseClasses} bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/30`;
      case "yellow":
        return `${baseClasses} bg-white dark:bg-slate-800 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700 hover:bg-yellow-50 dark:hover:bg-yellow-900/30`;
      case "orange":
        return `${baseClasses} bg-white dark:bg-slate-800 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/30`;
      case "green":
        return `${baseClasses} bg-white dark:bg-slate-800 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700 hover:bg-green-50 dark:hover:bg-green-900/30`;
      case "red":
        return `${baseClasses} bg-white dark:bg-slate-800 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700 hover:bg-red-50 dark:hover:bg-red-900/30`;
      default:
        return `${baseClasses} bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700`;
    }
  }
}
