import React from "react";
import { BaseCard, BaseCardProps } from "@/components/common/Card/BaseCard";
import { OntologyGraph } from "@/types/ontology";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Network, Calendar } from "lucide-react";

export class OntologyCard extends BaseCard<OntologyGraph> {
  constructor(props: BaseCardProps<OntologyGraph>) {
    super(props);
    this.config = { showEdit: true, showDelete: true, showFooter: true, deleteEntityName: "l'ontologie" };
  }

  getEntityDisplayName(): string {
    return `l'ontologie "${this.props.data.name}"`;
  }

  renderHeader() {
    const { name } = this.props.data;
    return (
      <div className="flex items-center gap-2">
        <Network className="h-5 w-5 text-primary" />
        <CardTitle className="text-lg">{name}</CardTitle>
      </div>
    );
  }

  renderContent() {
    const { description, node_count, edge_count } = this.props.data;
    return (
      <div className="space-y-2">
        {description && <CardDescription className="line-clamp-2">{description}</CardDescription>}
        <div className="text-sm text-muted-foreground">
          {node_count} nœud{node_count > 1 ? "s" : ""} · {edge_count} lien{edge_count > 1 ? "s" : ""}
        </div>
      </div>
    );
  }

  renderFooter() {
    return <div className="flex items-center gap-1 text-xs text-muted-foreground w-full">
      <Calendar className="h-3 w-3" />
      <span>{new Date(this.props.data.created_at).toLocaleDateString("fr-FR")}</span>
    </div>;
  }
}
