import React from "react";
import { BaseCard, BaseCardProps } from "./BaseCard";
import { Issue, IssueStatus } from "@/types/issue";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle, Sparkles } from "lucide-react";

interface IssueCardProps extends BaseCardProps<Issue> {
  onAssignToCopilot?: (id: string) => void;
}

export class IssueCard extends BaseCard<Issue> {
  declare props: IssueCardProps;

  getStatusIcon() {
    const { status } = this.props.data;
    switch (status) {
      case "open":
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
      case "closed":
        return <CheckCircle className="h-5 w-5 text-gray-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
    }
  }

  getStatusColor() {
    const { status } = this.props.data;
    const colors: Record<IssueStatus, string> = {
      open: "bg-blue-100 text-blue-800",
      closed: "bg-gray-100 text-gray-800",
    };
    return colors[status];
  }

  renderHeader() {
    const { data } = this.props;
    return (
      <>
        <div className="flex items-center gap-2">
          {this.getStatusIcon()}
          <CardTitle className="flex-1">{data.title}</CardTitle>
          {data.number && <span className="text-sm text-gray-500">#{data.number}</span>}
        </div>
      </>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="space-y-3">
        <CardDescription className="line-clamp-3">{data.description}</CardDescription>

        <div className="flex gap-2 flex-wrap">
          <Badge className={this.getStatusColor()}>{data.status}</Badge>
          {data.labels &&
            data.labels.length > 0 &&
            data.labels.map((label, idx) => (
              <Badge key={idx} variant="outline">
                {label}
              </Badge>
            ))}
          {data.assigned_to_copilot && (
            <Badge className="bg-purple-100 text-purple-800">
              <Sparkles className="h-3 w-3 mr-1" />
              Copilot
            </Badge>
          )}
        </div>

        {data.html_url && (
          <a href={data.html_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            View Issue
          </a>
        )}
      </div>
    );
  }

  renderFooter() {
    const { data } = this.props;

    return (
      <>
        {data.status === "open" && !data.assigned_to_copilot && (
          <Button
            variant="default"
            size="sm"
            className="bg-purple-600 hover:bg-purple-700"
            onClick={(e) => {
              e.stopPropagation();
              this.props.onAssignToCopilot?.(data.id);
            }}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Copilot Dev
          </Button>
        )}
      </>
    );
  }
}
