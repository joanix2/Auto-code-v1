import React from "react";
import { BaseCard, BaseCardProps } from "./BaseCard";
import { Repository } from "@/types/repository";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GitBranch, Lock, Unlock } from "lucide-react";

interface RepositoryCardProps extends BaseCardProps<Repository> {
  onSync?: (id: string) => void;
}

export class RepositoryCard extends BaseCard<Repository> {
  declare props: RepositoryCardProps;

  renderHeader() {
    const { data } = this.props;
    return (
      <>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            {data.name}
          </CardTitle>
          {data.is_private ? <Lock className="h-4 w-4 text-gray-500" /> : <Unlock className="h-4 w-4 text-gray-500" />}
        </div>
        <CardDescription>{data.full_name}</CardDescription>
      </>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="space-y-2">
        {data.description && <p className="text-sm text-gray-600 line-clamp-2">{data.description}</p>}
        <div className="flex gap-2">
          <Badge variant="outline">{data.default_branch}</Badge>
        </div>
      </div>
    );
  }

  renderFooter() {
    return (
      <Button
        variant="secondary"
        size="sm"
        onClick={(e) => {
          e.stopPropagation();
          this.props.onSync?.(this.props.data.id);
        }}
      >
        Sync Issues
      </Button>
    );
  }
}
