import React from "react";
import { BaseCard, BaseCardProps } from "./BaseCard";
import { Repository } from "@/types/repository";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Github, Lock, Trash2 } from "lucide-react";
import { AlertDialog } from "@/components/AlertDialog";

interface RepositoryCardProps extends BaseCardProps<Repository> {
  onSync?: (id: string) => void;
}

export class RepositoryCard extends BaseCard<Repository> {
  declare props: RepositoryCardProps;
  state = {
    showDeleteDialog: false,
  };

  constructor(props: RepositoryCardProps) {
    super(props);
    // Désactiver les boutons Edit et Delete par défaut
    this.config = {
      showEdit: false,
      showDelete: false,
      showFooter: true,
    };
  }

  handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    this.setState({ showDeleteDialog: true });
  };

  handleConfirmDelete = (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    this.setState({ showDeleteDialog: false });
    // Use setTimeout to ensure dialog closes before triggering navigation
    setTimeout(() => {
      this.props.onDelete?.(this.props.data.id);
    }, 0);
  };

  renderHeader() {
    const { data } = this.props;
    return (
      <>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              {data.name}
              {data.is_private && (
                <Badge variant="secondary" className="text-xs">
                  <Lock className="w-3 h-3 mr-1" />
                  Privé
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="mt-1">{data.description || "Aucune description"}</CardDescription>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-red-600 hover:bg-red-50" onClick={this.handleDeleteClick}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <AlertDialog
          open={this.state.showDeleteDialog}
          onOpenChange={(open) => this.setState({ showDeleteDialog: open })}
          title="Supprimer le repository"
          description={`Êtes-vous sûr de vouloir supprimer le repository "${data.name}" ? Cette action est irréversible.`}
          variant="error"
          icon={Trash2}
          closeLabel="Annuler"
          confirmLabel="Supprimer"
          onConfirm={this.handleConfirmDelete}
        />
      </>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="text-xs text-gray-500 space-y-1">
        {data.github_created_at && (
          <div className="flex items-center gap-2">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Créé le {this.formatDate(data.github_created_at)}</span>
          </div>
        )}
        {data.github_pushed_at && (
          <div className="flex items-center gap-2">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Dernier commit le {this.formatDate(data.github_pushed_at)}</span>
          </div>
        )}
      </div>
    );
  }

  renderFooter() {
    const { data } = this.props;
    const githubUrl = data.url || data.html_url || `https://github.com/${data.full_name}`;

    return (
      <div className="flex flex-col gap-2 w-full">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={(e) => {
            e.stopPropagation();
            window.open(githubUrl, "_blank");
          }}
        >
          <Github className="h-4 w-4 mr-2" />
          Voir le Projet
        </Button>
        <Button
          variant="default"
          size="sm"
          className="w-full bg-[#1e1b4b] hover:bg-[#312e81] text-white"
          onClick={(e) => {
            e.stopPropagation();
            this.props.onClick?.(data.id);
          }}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
            />
          </svg>
          Gérer les Tickets
        </Button>
      </div>
    );
  }

  private formatDate(dateString: string): string {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
  }
}
