import React, { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { IssueList } from "@/components/common/CardList/IssueList";
import { IssueStatusFilter } from "@/components/common/IssueStatusFilter";
import { useIssues } from "@/hooks/useIssues";
import { useRepositories } from "@/hooks/useRepositories";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { AssignToCopilotDialog } from "@/components/common/AssignToCopilotDialog";
import { Repository } from "@/types";
import { IssueStatus } from "@/types/issue";
import { useToast } from "@/components/ui/use-toast";

export function Issues() {
  const navigate = useNavigate();
  const { repositoryId } = useParams<{ repositoryId?: string }>();
  const { issues, loading, loadIssues, assignToCopilot, deleteIssue, syncIssues } = useIssues(repositoryId);
  const { getRepository } = useRepositories();
  const { toast } = useToast();

  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [assignLoading, setAssignLoading] = useState(false);
  const [repository, setRepository] = useState<Repository | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<IssueStatus | "all">("all");

  const selectedIssue = issues.find((issue) => issue.id === selectedIssueId);

  // Filter issues by status
  const filteredIssues = useMemo(() => {
    if (selectedStatus === "all") {
      return issues;
    }
    return issues.filter((issue) => issue.status === selectedStatus);
  }, [issues, selectedStatus]);

  // Calculate counts for each status
  const statusCounts = useMemo(() => {
    const counts = {
      all: issues.length,
      open: 0,
      in_progress: 0,
      review: 0,
      closed: 0,
      cancelled: 0,
    };

    issues.forEach((issue) => {
      counts[issue.status] = (counts[issue.status] || 0) + 1;
    });

    return counts;
  }, [issues]);

  // Load repository info if repositoryId is present
  useEffect(() => {
    if (repositoryId) {
      getRepository(repositoryId)
        .then(setRepository)
        .catch((error) => console.error("Failed to load repository:", error));
    }
  }, [repositoryId, getRepository]);

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

      toast({
        title: "✅ Assignation réussie",
        description: `${result.message}\n\nSurveillez vos notifications GitHub pour la PR.`,
      });

      setAssignDialogOpen(false);
      setSelectedIssueId(null);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "❌ Erreur d'assignation",
        description: (error as Error).message,
      });
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

  const handleViewMessages = (issueId: string) => {
    navigate(`/issues/${issueId}/messages`);
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
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{repository ? `${repository.name} - Issues` : "Issues"}</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">
          {repositoryId ? (repository ? `View and manage issues for ${repository.full_name || repository.name}` : "View and manage issues for this repository") : "View and manage all issues"}
        </p>
      </div>

      {/* Status Filter */}
      <IssueStatusFilter selectedStatus={selectedStatus} onStatusChange={setSelectedStatus} counts={statusCounts} />

      <IssueList
        items={filteredIssues}
        loading={loading}
        onSync={repositoryId ? handleSyncIssues : undefined}
        onAssignToCopilot={handleAssignToCopilot}
        onViewMessages={handleViewMessages}
        onClick={handleIssueClick}
        onEdit={handleEditIssue}
        onDelete={handleDeleteIssue}
        createUrl={repositoryId ? `/issues/new?repository=${repositoryId}` : undefined}
      />

      <AssignToCopilotDialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen} onConfirm={handleConfirmAssign} issueName={selectedIssue?.title || ""} loading={assignLoading} />
    </div>
  );
}
