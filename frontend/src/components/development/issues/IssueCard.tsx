import React from "react";
import { BaseCard, BaseCardProps, CardConfig } from "../../common/Card/BaseCard";
import { Issue, IssueStatus } from "@/types/issue";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle, Sparkles, Github } from "lucide-react";

interface IssueCardProps extends BaseCardProps<Issue> {
  onAssignToCopilot?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export class IssueCard extends BaseCard<Issue> {
  declare props: IssueCardProps;

  config: CardConfig = {
    showEdit: true,
    showDelete: true,
    showFooter: true,
    deleteEntityName: "le ticket",
  };

  getEntityDisplayName(): string {
    return `le ticket "${this.props.data.title}"`;
  }

  getStatusIcon() {
    const { status } = this.props.data;
    switch (status) {
      case "open":
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
      case "in_progress":
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case "review":
        return <AlertCircle className="h-5 w-5 text-purple-500" />;
      case "closed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
    }
  }

  getStatusColor() {
    const { status } = this.props.data;
    const colors: Record<IssueStatus, string> = {
      open: "bg-blue-100 text-blue-800",
      in_progress: "bg-yellow-100 text-yellow-800",
      review: "bg-purple-100 text-purple-800",
      closed: "bg-green-100 text-green-800",
      cancelled: "bg-gray-100 text-gray-800",
    };
    return colors[status];
  }

  renderHeader() {
    const { data } = this.props;
    return (
      <div className="flex items-start gap-2">
        {this.getStatusIcon()}
        <div className="flex-1 flex flex-col gap-1">
          <CardTitle>{data.title}</CardTitle>
          {data.github_issue_number && <span className="text-sm text-gray-500">#{data.github_issue_number}</span>}
        </div>
      </div>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="space-y-3">
        <CardDescription className="line-clamp-3">{data.description}</CardDescription>

        <div className="flex gap-2 flex-wrap">
          <Badge className={this.getStatusColor()}>{data.status}</Badge>
          {data.assigned_to_copilot && (
            <Badge className="bg-purple-100 text-purple-800">
              <Sparkles className="h-3 w-3 mr-1" />
              Copilot
            </Badge>
          )}
        </div>
      </div>
    );
  }

  renderFooter() {
    const { data } = this.props;

    // Debug: log pour vérifier les champs GitHub
    if (data.github_issue_number && !data.github_issue_url) {
      console.log(`Issue #${data.github_issue_number} n'a pas de github_issue_url`, data);
    }

    return (
      <div className="flex flex-col gap-2 w-full">
        {data.github_issue_url && (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={(e) => {
              e.stopPropagation();
              window.open(data.github_issue_url, "_blank");
            }}
          >
            <Github className="h-4 w-4 mr-2" />
            Voir sur GitHub
          </Button>
        )}
        {data.status === "open" && !data.assigned_to_copilot && (
          <Button
            variant="default"
            size="sm"
            className="bg-purple-600 hover:bg-purple-700 w-full"
            onClick={(e) => {
              e.stopPropagation();
              this.props.onAssignToCopilot?.(data.id);
            }}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Copilot Dev
          </Button>
        )}
      </div>
    );
  }
}
