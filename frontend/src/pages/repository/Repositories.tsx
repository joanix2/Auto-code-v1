import React from "react";
import { useNavigate, Link } from "react-router-dom";
import { RepositoryList } from "@/components/common/CardList/RepositoryList";
import { useRepositories } from "@/hooks/useRepositories";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Repositories() {
  const navigate = useNavigate();
  const { repositories, loading, error, syncRepositories, syncIssues, deleteRepository } = useRepositories();

  const handleSyncRepositories = async () => {
    await syncRepositories();
  };

  const handleSyncIssues = async (repoId: string) => {
    await syncIssues(repoId);
  };

  const handleDeleteRepository = async (repoId: string) => {
    await deleteRepository(repoId);
  };

  const handleEditRepository = (repoId: string) => {
    navigate(`/development/repositories/${repoId}/edit`);
  };

  const handleRepositoryClick = (repoId: string) => {
    navigate(`/development/repositories/${repoId}/issues`);
  };

  const isGitHubNotConnected = error?.includes("GitHub account not connected");

  return (
    <div className="container mx-auto max-w-7xl p-3 sm:p-6">
      <div className="mb-4 sm:mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Repositories</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">Manage your GitHub repositories and sync issues</p>
      </div>

      {isGitHubNotConnected && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" asChild className="ml-4">
              <Link to="/profile">
                <Settings className="h-4 w-4 mr-2" />
                Go to Profile
              </Link>
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <RepositoryList
        items={repositories}
        loading={loading}
        onSync={handleSyncRepositories}
        onSyncIssues={handleSyncIssues}
        onClick={handleRepositoryClick}
        onEdit={handleEditRepository}
        onDelete={handleDeleteRepository}
        createUrl="/development/repositories/new"
      />
    </div>
  );
}
