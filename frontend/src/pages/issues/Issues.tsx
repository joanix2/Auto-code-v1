import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { IssueList } from "@/components/common/CardList/IssueList";
import { useIssues } from "@/hooks/useIssues";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export function Issues() {
  const navigate = useNavigate();
  const { repositoryId } = useParams<{ repositoryId?: string }>();
  const { issues, loading, loadIssues, assignToCopilot, deleteIssue } = useIssues(repositoryId);

  const handleAssignToCopilot = async (issueId: string) => {
    await assignToCopilot(issueId);
  };

  const handleDeleteIssue = async (issueId: string) => {
    if (confirm("Are you sure you want to delete this issue?")) {
      await deleteIssue(issueId);
    }
  };

  const handleIssueClick = (issueId: string) => {
    navigate(`/issues/${issueId}`);
  };

  const handleSyncIssues = async () => {
    await loadIssues();
  };

  return (
    <div className="container mx-auto max-w-7xl p-3 sm:p-6">
      <div className="mb-4 sm:mb-6">
        {repositoryId && (
          <Button variant="ghost" size="sm" onClick={() => navigate("/repositories")} className="mb-3 sm:mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Repositories
          </Button>
        )}
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Issues</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">{repositoryId ? "View and manage issues for this repository" : "View and manage all issues"}</p>
      </div>

      <IssueList
        items={issues}
        loading={loading}
        onSync={repositoryId ? handleSyncIssues : undefined}
        onAssignToCopilot={handleAssignToCopilot}
        onClick={handleIssueClick}
        onDelete={handleDeleteIssue}
        createUrl={repositoryId ? `/issues/new?repository=${repositoryId}` : undefined}
      />
    </div>
  );
}
