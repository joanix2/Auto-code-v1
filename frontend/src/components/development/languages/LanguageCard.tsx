import React from "react";
import { BaseCard } from "@/components/common/Card/BaseCard";
import { FileText } from "lucide-react";
import type { Language } from "@/services/languageService";

export class LanguageCard extends BaseCard<Language> {
  getEntityDisplayName(): string {
    return this.props.data.name;
  }

  renderHeader(): React.ReactNode {
    const { name, node_count, edge_count } = this.props.data;
    return (
      <div className="flex items-center gap-3">
        <FileText className="w-5 h-5 text-blue-500 shrink-0" />
        <div className="min-w-0">
          <h3 className="font-medium truncate">{name}</h3>
          <p className="text-sm text-gray-500">
            {node_count} nœuds · {edge_count} arêtes
          </p>
        </div>
      </div>
    );
  }

  renderContent(): React.ReactNode {
    return null;
  }

  renderFooter(): React.ReactNode {
    return null;
  }
}
