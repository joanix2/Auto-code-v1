import React from "react";
import { BaseCardList } from "@/components/common/CardList/BaseCardList";
import { DSLCard } from "./DSLCard";
import { DSLGraph } from "@/types/dsl";

interface DSLListProps {
  items: DSLGraph[];
  onSync?: () => Promise<void>;
  onSearch?: (query: string) => void;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
  onClick?: (id: string) => void;
  loading?: boolean;
  createUrl?: string;
  showSync?: boolean;
}

export class DSLList extends BaseCardList<DSLGraph> {
  declare props: DSLListProps;

  renderCard(dsl: DSLGraph): React.ReactNode {
    return <DSLCard data={dsl} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage(): string {
    return "Aucun DSL trouvé. Créez votre premier DSL pour commencer.";
  }

  getSyncButtonLabel(): string {
    return "Synchroniser";
  }

  getCreateButtonLabel(): string {
    return "Nouveau DSL";
  }
}
