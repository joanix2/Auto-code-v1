import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import type { Repository } from "@/types";

function Projects() {
  const { user, signOut } = useAuth();
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
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
        {/* Navigation Tabs */}
        <div className="mb-6 flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
          <Link to="/projects">
            <Button variant="ghost" className="rounded-b-none border-b-2 border-blue-600 font-medium text-blue-600">
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              Mes Projets
            </Button>
          </Link>
          <Link to="/create-ticket">
            <Button variant="ghost" className="rounded-b-none hover:border-b-2 hover:border-slate-300">
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Nouveau ticket
            </Button>
          </Link>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6 flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
          <Link to="/projects">
            <Button variant="ghost" className="rounded-b-none border-b-2 border-blue-600 font-medium text-blue-600">
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              Mes Projets
            </Button>
          </Link>
          <Link to="/create-ticket">
            <Button variant="ghost" className="rounded-b-none hover:border-b-2 hover:border-slate-300">
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Nouveau ticket
            </Button>
          </Link>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between flex-wrap gap-4">
              <h2 className="text-3xl font-bold tracking-tight">
                {projects.length} projet{projects.length !== 1 ? "s" : ""}
              </h2>
              <div className="flex gap-2">
                <Dialog open={syncDialogOpen} onOpenChange={setSyncDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="default" size="sm">
                      <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                      </svg>
                      Sync GitHub
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Synchroniser avec GitHub</DialogTitle>
                      <DialogDescription>
                        Entrez votre token d'accès personnel GitHub pour synchroniser vos repositories.
                        <a href="https://github.com/settings/tokens/new?scopes=repo" target="_blank" rel="noopener noreferrer" className="block mt-2 text-blue-600 hover:underline text-sm">
                          Créer un token GitHub →
                        </a>
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="github-token">Token GitHub</Label>
                        <Input id="github-token" type="password" placeholder="ghp_xxxxxxxxxxxx" value={githubToken} onChange={(e) => setGithubToken(e.target.value)} disabled={syncing} />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setSyncDialogOpen(false)} disabled={syncing}>
                        Annuler
                      </Button>
                      <Button onClick={syncGitHubRepos} disabled={syncing || !githubToken.trim()}>
                        {syncing ? "Synchronisation..." : "Synchroniser"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
                <Button onClick={fetchProjects} variant="outline" size="sm">
                  <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Actualiser
                </Button>
              </div>
            </div>

            {projects.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <svg className="mb-4 h-16 w-16 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  <p className="mb-4 text-muted-foreground">Aucun projet trouvé</p>
                  <Button asChild>
                    <a href="https://github.com/new" target="_blank" rel="noopener noreferrer">
                      Créer un nouveau projet sur GitHub
                    </a>
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {projects.map((project) => (
                  <Card key={project.id} className="flex flex-col overflow-hidden transition-all hover:shadow-lg">
                    <CardHeader>
                      <div className="flex items-start justify-between gap-2">
                        <CardTitle className="line-clamp-1">{project.name}</CardTitle>
                        <Badge variant={project.private ? "secondary" : "default"}>{project.private ? "Privé" : "Public"}</Badge>
                      </div>
                      <CardDescription className="line-clamp-2">{project.description || "Aucune description"}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-1 flex-col justify-between gap-4">
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div className="flex items-center gap-3">
                          {project.language && (
                            <span className="flex items-center gap-1">
                              <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                              {project.language}
                            </span>
                          )}
                        </div>
                        <div className="text-xs">Mis à jour le {formatDate(project.updated_at || project.created_at)}</div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <Button variant="outline" size="sm" asChild>
                          <a href={project.url} target="_blank" rel="noopener noreferrer">
                            <svg className="mr-2 h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                            Voir sur GitHub
                          </a>
                        </Button>
                        <Button size="sm" asChild>
                          <Link to={`/create-ticket?repo=${project.full_name}`}>Créer un ticket</Link>
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default Projects;
