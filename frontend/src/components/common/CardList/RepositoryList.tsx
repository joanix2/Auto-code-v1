import React from "react";
import { BaseCardList, BaseCardListProps } from "./BaseCardList";
import { RepositoryCard } from "../Card/RepositoryCard";
import { Repository } from "@/types/repository";

interface RepositoryListProps extends BaseCardListProps<Repository> {
  onSyncIssues?: (repoId: string) => void;
  onDelete?: (repoId: string) => void;
  onEdit?: (repoId: string) => void;
  onClick?: (repoId: string) => void;
}

export class RepositoryList extends BaseCardList<Repository> {
  declare props: RepositoryListProps;

  renderCard(repo: Repository) {
    return <RepositoryCard data={repo} onSync={this.props.onSyncIssues} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage() {
    return 'No repositories found. Click "Sync Repositories" to get started.';
  }

  getSyncButtonLabel() {
    return "Sync Repositories";
  }
}
