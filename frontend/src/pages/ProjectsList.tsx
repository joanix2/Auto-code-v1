import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { RepositoryCard } from "@/components/RepositoryCard";
import type { Repository } from "@/types";

function ProjectsList() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError("");

      // Récupérer les repositories depuis notre API backend
      const repos = await apiClient.getRepositories();
      setProjects(repos);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la récupération des projets");
    } finally {
      setLoading(false);
    }
  };

  const syncGitHubRepos = async () => {
    if (!githubToken.trim()) {
      setError("Veuillez entrer un token GitHub valide");
      return;
    }

    try {
      setSyncing(true);
      setError("");

      const response = await fetch("http://localhost:8000/api/repositories/sync-github", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "X-GitHub-Token": githubToken,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Échec de la synchronisation");
      }

      const data = await response.json();
      await fetchProjects(); // Recharger la liste
      setSyncDialogOpen(false);
      setGithubToken(""); // Reset token
      setError("");
      alert(`${data.synced} repository(s) synchronisé(s) avec succès!`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la synchronisation");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:border-slate-800 dark:bg-slate-950/95">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-8 max-w-7xl">
          <Link to="/projects" className="flex items-center gap-3 transition-opacity hover:opacity-80">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 shadow-md">
              <span className="text-xl">📦</span>
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent leading-tight">Auto-Code Platform</h1>
              <span className="text-xs text-slate-500 dark:text-slate-400">Gestion de projets</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            {user && (
              <div className="text-sm text-slate-600 dark:text-slate-400 hidden sm:block">
                <span className="font-medium">{user.username}</span>
              </div>
            )}
            <Button onClick={signOut} variant="ghost" size="sm" className="text-slate-600 hover:text-red-600">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </Button>
          </div>
        </div>
      </header>

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
            <Dialog open={syncDialogOpen} onOpenChange={setSyncDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-slate-300 hover:bg-slate-50">
                  <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                  Sync GitHub
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Synchroniser avec GitHub</DialogTitle>
                  <DialogDescription>Entrez votre token GitHub pour synchroniser vos repositories</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="github-token">Token GitHub</Label>
                    <Input id="github-token" type="password" placeholder="ghp_xxxxxxxxxxxx" value={githubToken} onChange={(e) => setGithubToken(e.target.value)} />
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={syncGitHubRepos} disabled={syncing || !githubToken.trim()} className="w-full">
                    {syncing ? "Synchronisation..." : "Synchroniser"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
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
              <p className="text-slate-600 dark:text-slate-400 mb-4">Commencez par créer un nouveau repository ou synchroniser avec GitHub</p>
              <div className="flex gap-2">
                <Button onClick={() => navigate("/new-repository")} variant="outline">
                  Créer un repository
                </Button>
                <Button onClick={() => setSyncDialogOpen(true)}>Sync GitHub</Button>
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
