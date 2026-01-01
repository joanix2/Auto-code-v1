import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RepositoryCard } from "@/components/RepositoryCard";
import { AppBar } from "@/components/AppBar";
import { Input } from "@/components/ui/input";
import type { Repository } from "@/types";

// Fonction de distance de Levenshtein
function levenshteinDistance(str1: string, str2: string): number {
  const s1 = str1.toLowerCase();
  const s2 = str2.toLowerCase();

  const matrix: number[][] = [];

  for (let i = 0; i <= s2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= s1.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= s2.length; i++) {
    for (let j = 1; j <= s1.length; j++) {
      if (s2.charAt(i - 1) === s1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
      }
    }
  }

  return matrix[s2.length][s1.length];
}

function ProjectsList() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Repository[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<Repository[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
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
          const syncResult = await syncGitHubRepos();
          if (syncResult?.deleted > 0) {
            console.log(`✅ ${syncResult.deleted} repository(ies) supprimé(s) de la base de données`);
          }
          if (syncResult?.synced > 0) {
            console.log(`✅ ${syncResult.synced} repository(ies) synchronisé(s)`);
          }
        } catch (syncError) {
          console.warn("Sync failed, continuing with local repos:", syncError);
        }
      }

      // Récupérer les repositories depuis notre API backend
      const repos = await apiClient.getRepositories();

      // Trier par date du dernier push GitHub (plus récent en premier)
      const sortedRepos = repos.sort((a, b) => {
        const dateA = new Date(a.github_pushed_at || a.github_updated_at || a.github_created_at || a.created_at).getTime();
        const dateB = new Date(b.github_pushed_at || b.github_updated_at || b.github_created_at || b.created_at).getTime();
        return dateB - dateA; // Ordre décroissant (plus récent d'abord)
      });

      setProjects(sortedRepos);
      setFilteredProjects(sortedRepos);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la récupération des projets");
    } finally {
      setLoading(false);
    }
  }, [user?.github_token, syncGitHubRepos]);

  // Filtrage avec distance de Levenshtein
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredProjects(projects);
      return;
    }

    const query = searchQuery.toLowerCase();
    const threshold = 3; // Distance maximale acceptable

    const filtered = projects
      .map((project) => {
        const nameDistance = levenshteinDistance(project.name, query);
        const fullNameDistance = project.full_name ? levenshteinDistance(project.full_name, query) : Infinity;
        const descriptionDistance = project.description ? levenshteinDistance(project.description, query) : Infinity;

        // Prendre la meilleure correspondance
        const bestDistance = Math.min(nameDistance, fullNameDistance, descriptionDistance);

        // Si le nom contient la requête (recherche partielle), priorité
        const nameContains = project.name.toLowerCase().includes(query);
        const fullNameContains = project.full_name?.toLowerCase().includes(query);
        const descriptionContains = project.description?.toLowerCase().includes(query);

        return {
          project,
          score: nameContains || fullNameContains || descriptionContains ? -1 : bestDistance,
        };
      })
      .filter((item) => item.score === -1 || item.score <= threshold)
      .sort((a, b) => a.score - b.score)
      .map((item) => item.project);

    setFilteredProjects(filtered);
  }, [searchQuery, projects]);

  useEffect(() => {
    fetchAndSyncProjects();
  }, [fetchAndSyncProjects]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppBar />

      {/* Content */}
      <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
        {/* Projects Header */}
        <div className="flex flex-col gap-4 mb-8">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Mes Projets</h2>
            <p className="text-slate-600 dark:text-slate-400 mt-1">Gérez et consultez vos repositories</p>
          </div>

          {/* Search Bar with Add Button */}
          <div className="flex gap-3 items-center">
            <div className="relative flex-1">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <Input
                type="text"
                placeholder="Rechercher un repository..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border-slate-300 focus:border-blue-500 focus:ring-blue-500"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <Link to="/new-repository">
              <Button size="icon" className="h-10 w-10 bg-blue-600 hover:bg-blue-700 text-white shadow-md">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
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
        ) : filteredProjects.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg className="h-12 w-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Aucun résultat</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">Aucun repository ne correspond à "{searchQuery}"</p>
              <Button onClick={() => setSearchQuery("")} variant="outline">
                Effacer la recherche
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <RepositoryCard key={project.id} repository={project} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default ProjectsList;
