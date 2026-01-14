import React from "react";
import { BaseCardList } from "@/components/common/CardList/BaseCardList";
import { MetamodelCard } from "./MetamodelCard";
import { Metamodel } from "@/types/metamodel";

interface MetamodelListProps {
  items: Metamodel[];
  onSync?: () => Promise<void>;
  onSearch?: (query: string) => void;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
  onClick?: (id: string) => void;
  loading?: boolean;
  createUrl?: string;
  showSync?: boolean;
}

export class MetamodelList extends BaseCardList<Metamodel> {
  declare props: MetamodelListProps;

  renderCard(metamodel: Metamodel): React.ReactNode {
    return <MetamodelCard data={metamodel} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage(): string {
    return "Aucun métamodèle trouvé. Créez votre premier métamodèle pour commencer.";
  }

  getSyncButtonLabel(): string {
    return "Synchroniser";
  }

  getCreateButtonLabel(): string {
    return "Nouveau métamodèle";
  }
}
