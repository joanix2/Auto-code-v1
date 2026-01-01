import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RepositoryCard } from "@/components/RepositoryCard";
import { AppBar } from "@/components/AppBar";
import type { Repository } from "@/types";

function ProjectsList() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const syncGitHubRepos = useCallback(async () => {
    if (!user?.github_token) {
      return;
    }

    const response = await fetch("http://localhost:8000/api/repositories/sync-github", {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        "X-GitHub-Token": user.github_token,
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Échec de la synchronisation");
    }

    return response.json();
  }, [user?.github_token]);

  const fetchAndSyncProjects = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      // Si l'utilisateur a un token GitHub, synchroniser automatiquement
      if (user?.github_token) {
        try {
          await syncGitHubRepos();
        } catch (syncError) {
          console.warn("Sync failed, continuing with local repos:", syncError);
        }
      }

      // Récupérer les repositories depuis notre API backend
      const repos = await apiClient.getRepositories();
      setProjects(repos);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la récupération des projets");
    } finally {
      setLoading(false);
    }
  }, [user?.github_token, syncGitHubRepos]);

  useEffect(() => {
    fetchAndSyncProjects();
  }, [fetchAndSyncProjects]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppBar />

      {/* Content */}
      <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
        {/* Projects Header */}
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Mes Projets</h2>
            <p className="text-slate-600 dark:text-slate-400 mt-1">Gérez et consultez vos repositories</p>
          </div>
          <div className="flex gap-3">
            <Link to="/new-repository">
              <Button variant="outline" className="border-slate-300 hover:bg-slate-50">
                <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Nouveau Repository
              </Button>
            </Link>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Projects Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-slate-600 dark:text-slate-400">Chargement des projets...</div>
          </div>
        ) : projects.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg className="h-12 w-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Aucun projet</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                {user?.github_token ? "Commencez par créer un nouveau repository" : "Commencez par créer un nouveau repository ou configurer votre compte GitHub dans votre profil"}
              </p>
              <div className="flex gap-2">
                <Button onClick={() => navigate("/new-repository")} variant="outline">
                  Créer un repository
                </Button>
                {!user?.github_token && <Button onClick={() => navigate("/profile")}>Configurer GitHub</Button>}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <RepositoryCard key={project.id} repository={project} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default ProjectsList;
