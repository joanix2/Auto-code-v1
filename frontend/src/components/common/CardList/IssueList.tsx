import React from "react";
import { BaseCardList, BaseCardListProps } from "./BaseCardList";
import { IssueCard } from "../Card/IssueCard";
import { Issue } from "@/types/issue";

interface IssueListProps extends BaseCardListProps<Issue> {
  onAssignToCopilot?: (issueId: string) => void;
  onDelete?: (issueId: string) => void;
  onEdit?: (issueId: string) => void;
  onClick?: (issueId: string) => void;
}

export class IssueList extends BaseCardList<Issue> {
  declare props: IssueListProps;

  renderCard(issue: Issue) {
    return <IssueCard data={issue} onAssignToCopilot={this.props.onAssignToCopilot} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage() {
    return 'No issues found. Click "Sync Issues" to import from GitHub.';
  }

  getSyncButtonLabel() {
    return "Sync Issues";
  }
}
