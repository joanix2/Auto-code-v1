import React from "react";
import { BaseCard, BaseCardProps } from "../../common/Card/BaseCard";
import { Project } from "@/types/project";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock } from "lucide-react";
import { formatRelativeTime, formatDate } from "@/utils/dateFormatter";

const statusLabels: Record<string, { label: string; variant: "default" | "secondary" | "outline" }> = {
  draft: { label: "Brouillon", variant: "outline" },
  active: { label: "Actif", variant: "default" },
  archived: { label: "Archivé", variant: "secondary" },
};

export class ProjectCard extends BaseCard<Project> {
  constructor(props: BaseCardProps<Project>) {
    super(props);
    this.config = {
      showEdit: true,
      showDelete: true,
      showFooter: true,
      deleteEntityName: "le projet",
    };
  }

  getEntityDisplayName(): string {
    return `le projet "${this.props.data.name}"`;
  }

  renderHeader() {
    const { data } = this.props;
    const status = statusLabels[data.status] || statusLabels.draft;
    return (
      <div className="flex-1">
        <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          {data.name}
          <Badge variant={status.variant} className="text-xs">
            {status.label}
          </Badge>
        </CardTitle>
        <CardDescription className="mt-1">{data.description || "Aucune description"}</CardDescription>
      </div>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="text-xs text-gray-600 space-y-2">
        <div className="flex items-center gap-2">
          <Calendar className="w-3.5 h-3.5 text-gray-400" />
          <span>Créé le {formatDate(data.created_at)}</span>
        </div>
        {data.updated_at && (
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-gray-400" />
            <span>Mis à jour {formatRelativeTime(data.updated_at)}</span>
          </div>
        )}
      </div>
    );
  }

  renderFooter() {
    return null;
  }
}
