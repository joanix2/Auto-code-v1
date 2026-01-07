import React from "react";
import { IssueStatus } from "@/types/issue";
import { cn } from "@/lib/utils";

interface IssueStatusFilterProps {
  selectedStatus: IssueStatus | "all";
  onStatusChange: (status: IssueStatus | "all") => void;
  counts?: {
    all: number;
    open: number;
    in_progress: number;
    review: number;
    closed: number;
    cancelled: number;
  };
}

const statusConfig = {
  all: {
    label: "Tous",
    textColor: "text-slate-700",
    borderColor: "border-slate-700",
    badgeColor: "bg-slate-700",
    hoverBg: "hover:bg-slate-50",
    activeBg: "bg-slate-100",
  },
  open: {
    label: "Ouvert",
    textColor: "text-purple-700",
    borderColor: "border-purple-700",
    badgeColor: "bg-purple-700",
    hoverBg: "hover:bg-purple-50",
    activeBg: "bg-purple-100",
  },
  in_progress: {
    label: "En cours",
    textColor: "text-amber-700",
    borderColor: "border-amber-700",
    badgeColor: "bg-amber-700",
    hoverBg: "hover:bg-amber-50",
    activeBg: "bg-amber-100",
  },
  review: {
    label: "En validation",
    textColor: "text-red-700",
    borderColor: "border-red-700",
    badgeColor: "bg-red-700",
    hoverBg: "hover:bg-red-50",
    activeBg: "bg-red-100",
  },
  closed: {
    label: "Fermé",
    textColor: "text-green-700",
    borderColor: "border-green-700",
    badgeColor: "bg-green-700",
    hoverBg: "hover:bg-green-50",
    activeBg: "bg-green-100",
  },
  cancelled: {
    label: "Annulé",
    textColor: "text-gray-700",
    borderColor: "border-gray-700",
    badgeColor: "bg-gray-700",
    hoverBg: "hover:bg-gray-50",
    activeBg: "bg-gray-100",
  },
};

export function IssueStatusFilter({ selectedStatus, onStatusChange, counts }: IssueStatusFilterProps) {
  const statuses: Array<IssueStatus | "all"> = ["all", "open", "in_progress", "review", "closed", "cancelled"];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-4 sm:mb-6">
      {statuses.map((status) => {
        const config = statusConfig[status];
        const isSelected = selectedStatus === status;
        const count = counts?.[status] ?? 0;

        return (
          <button
            key={status}
            onClick={() => onStatusChange(status)}
            className={cn(
              "h-12 px-4 rounded-lg font-medium text-sm transition-all duration-200",
              "flex items-center justify-between gap-3",
              "border-2",
              "focus:outline-none",
              // Bordure toujours colorée
              config.borderColor,
              // Non sélectionné : fond blanc, texte coloré
              !isSelected && "bg-white",
              !isSelected && config.textColor,
              !isSelected && config.hoverBg,
              // Sélectionné : fond coloré, texte blanc
              isSelected && config.badgeColor,
              isSelected && "text-white",
              isSelected && "shadow-lg"
            )}
          >
            <span className="whitespace-nowrap">{config.label}</span>
            {counts && (
              <span
                className={cn(
                  "px-2 py-0.5 text-xs font-bold min-w-[24px] text-center",
                  // Non sélectionné : texte coloré, pas de fond
                  !isSelected && config.textColor,
                  // Sélectionné : texte blanc, rien autour
                  isSelected && "text-white"
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
