import React from "react";
import { BaseCardList } from "@/components/common/CardList/BaseCardList";
import { LanguageCard } from "./LanguageCard";
import type { Language } from "@/services/languageService";

interface LanguageListProps {
  items: Language[];
  onDelete?: (id: string) => void;
  loading?: boolean;
  createUrl?: string;
}

export class LanguageList extends BaseCardList<Language> {
  private _onDelete: ((id: string) => void) | undefined;

  constructor(props: LanguageListProps) {
    super(props);
    this._onDelete = props.onDelete;
  }

  renderCard(item: Language): React.ReactNode {
    return (
      <LanguageCard
        key={item.id}
        data={item}
        onClick={(id) => { window.location.href = `/development/languages/${id}`; }}
        onDelete={this._onDelete}
      />
    );
  }

  getEmptyMessage(): string {
    return "Aucun langage défini. Créez votre premier langage !";
  }

  getSyncButtonLabel(): string {
    return "Synchroniser";
  }

  getCreateButtonLabel(): string {
    return "Nouveau langage";
  }
}
