import React from "react";
import { BaseCard, BaseCardProps } from "../../common/Card/BaseCard";
import { Repository } from "@/types/repository";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Github, Lock, Calendar, GitCommit } from "lucide-react";
import { formatRelativeTime, formatDate } from "@/utils/dateFormatter";

interface RepositoryCardProps extends BaseCardProps<Repository> {
  onSync?: (id: string) => void;
}

export class RepositoryCard extends BaseCard<Repository> {
  declare props: RepositoryCardProps;

  constructor(props: RepositoryCardProps) {
    super(props);
    // Activer les boutons Edit et Delete du BaseCard
    this.config = {
      showEdit: true,
      showDelete: true,
      showFooter: true,
      deleteEntityName: "le repository",
    };
  }

  getEntityDisplayName(): string {
    return `le repository "${this.props.data.name}"`;
  }

  renderHeader() {
    const { data } = this.props;
    return (
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
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="text-xs text-gray-600 space-y-2">
        {data.github_created_at && (
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-gray-400" />
            <span>Créé le {formatDate(data.github_created_at)}</span>
          </div>
        )}
        {data.github_pushed_at && (
          <div className="flex items-center gap-2">
            <GitCommit className="w-3.5 h-3.5 text-gray-400" />
            <span>Dernier commit {formatRelativeTime(data.github_pushed_at)}</span>
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
}
