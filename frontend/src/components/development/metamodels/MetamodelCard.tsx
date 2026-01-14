import React from "react";
import { BaseCard } from "@/components/common/Card/BaseCard";
import { Metamodel } from "@/types/metamodel";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Database, GitBranch, Calendar } from "lucide-react";

interface MetamodelCardProps {
  data: Metamodel;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
  onClick?: (id: string) => void;
}

export class MetamodelCard extends BaseCard<Metamodel> {
  config = {
    showEdit: true,
    showDelete: true,
    showFooter: true,
    deleteEntityName: "le métamodèle",
  };

  getEntityDisplayName(): string {
    return `"${this.props.data.name}"`;
  }

  getStatusBadge(status?: string) {
    const statusConfig = {
      draft: { label: "Brouillon", variant: "secondary" as const },
      validated: { label: "Validé", variant: "default" as const },
      deprecated: { label: "Obsolète", variant: "destructive" as const },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  }

  renderHeader() {
    const { name, version, status } = this.props.data;
    return (
      <>
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-primary" />
          <CardTitle className="text-lg">{name}</CardTitle>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant="outline">v{version}</Badge>
          {this.getStatusBadge(status)}
        </div>
      </>
    );
  }

  renderContent() {
    const { description, concepts, relations, author } = this.props.data;
    return (
      <div className="space-y-3">
        {description && <CardDescription className="line-clamp-2">{description}</CardDescription>}

        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Database className="h-4 w-4" />
            <span>
              {concepts} concept{concepts > 1 ? "s" : ""}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <GitBranch className="h-4 w-4" />
            <span>
              {relations} relation{relations > 1 ? "s" : ""}
            </span>
          </div>
        </div>

        {author && (
          <div className="text-sm text-muted-foreground">
            <span className="font-medium">Auteur:</span> {author}
          </div>
        )}
      </div>
    );
  }

  renderFooter() {
    const { created_at, updated_at } = this.props.data;
    const date = updated_at || created_at;

    return (
      <div className="flex items-center gap-1 text-xs text-muted-foreground w-full">
        <Calendar className="h-3 w-3" />
        <span>{date ? new Date(date).toLocaleDateString("fr-FR") : "Date inconnue"}</span>
      </div>
    );
  }
}
