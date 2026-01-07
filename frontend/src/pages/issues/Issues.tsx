import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { IssueList } from "@/components/common/CardList/IssueList";
import { useIssues } from "@/hooks/useIssues";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { AssignToCopilotDialog } from "@/components/common/AssignToCopilotDialog";

export function Issues() {
  const navigate = useNavigate();
  const { repositoryId } = useParams<{ repositoryId?: string }>();
  const { issues, loading, loadIssues, assignToCopilot, deleteIssue, syncIssues } = useIssues(repositoryId);

  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [assignLoading, setAssignLoading] = useState(false);

  const selectedIssue = issues.find((issue) => issue.id === selectedIssueId);

  const handleAssignToCopilot = async (issueId: string) => {
    setSelectedIssueId(issueId);
    setAssignDialogOpen(true);
  };

  const handleConfirmAssign = async (customInstructions: string) => {
    if (!selectedIssueId) return;

    setAssignLoading(true);
    try {
      const result = await assignToCopilot(selectedIssueId, {
        custom_instructions: customInstructions || undefined,
      });

      alert(`✅ ${result.message}\n\nSurveillez vos notifications GitHub pour la PR.`);

      setAssignDialogOpen(false);
      setSelectedIssueId(null);
    } catch (error) {
      alert(`❌ Erreur d'assignation: ${(error as Error).message}`);
    } finally {
      setAssignLoading(false);
    }
  };

  const handleDeleteIssue = async (issueId: string) => {
    await deleteIssue(issueId);
  };

  const handleEditIssue = (issueId: string) => {
    navigate(`/issues/${issueId}/edit`);
  };

  const handleIssueClick = (issueId: string) => {
    navigate(`/issues/${issueId}`);
  };

  const handleSyncIssues = async () => {
    if (syncIssues) {
      await syncIssues();
    }
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
        onEdit={handleEditIssue}
        onDelete={handleDeleteIssue}
        createUrl={repositoryId ? `/issues/new?repository=${repositoryId}` : undefined}
      />

      <AssignToCopilotDialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen} onConfirm={handleConfirmAssign} issueName={selectedIssue?.title || ""} loading={assignLoading} />
    </div>
  );
}
