import React from "react";
import { useNavigate } from "react-router-dom";
import { RepositoryList } from "@/components/common/CardList/RepositoryList";
import { useRepositories } from "@/hooks/useRepositories";

export function Repositories() {
  const navigate = useNavigate();
  const { repositories, loading, syncRepositories, syncIssues, deleteRepository } = useRepositories();

  const handleSyncRepositories = async () => {
    await syncRepositories();
  };

  const handleSyncIssues = async (repoId: string) => {
    await syncIssues(repoId);
  };

  const handleDeleteRepository = async (repoId: string) => {
    if (confirm("Are you sure you want to delete this repository?")) {
      await deleteRepository(repoId);
    }
  };

  const handleRepositoryClick = (repoId: string) => {
    navigate(`/repositories/${repoId}/issues`);
  };

  return (
    <div className="container mx-auto max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Repositories</h1>
        <p className="mt-2 text-sm text-gray-600">Manage your GitHub repositories and sync issues</p>
      </div>

      <RepositoryList items={repositories} loading={loading} onSync={handleSyncRepositories} onSyncIssues={handleSyncIssues} onClick={handleRepositoryClick} onDelete={handleDeleteRepository} />
    </div>
  );
}
