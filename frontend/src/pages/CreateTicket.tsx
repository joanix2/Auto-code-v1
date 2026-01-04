import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppBar } from "@/components/AppBar";
import type { Repository } from "@/types";

interface TicketFormData {
  title: string;
  description: string;
  priority: string;
  type: string;
  status: string;
  repository: string;
}

function CreateTicket() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { ticketId } = useParams<{ ticketId?: string }>();
  const repositoryId = searchParams.get("repository");

  const isEditMode = !!ticketId;

  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [formData, setFormData] = useState<TicketFormData>({
    title: "",
    description: "",
    priority: "medium",
    type: "feature",
    status: "open",
    repository: repositoryId || "",
  });
  const [loading, setLoading] = useState(false);
  const [loadingTicket, setLoadingTicket] = useState(isEditMode);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchRepositories();
  }, []);

  useEffect(() => {
    if (repositoryId && !isEditMode) {
      setFormData((prev) => ({ ...prev, repository: repositoryId }));
    }
  }, [repositoryId, isEditMode]);

  useEffect(() => {
    if (isEditMode && ticketId) {
      fetchTicket();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketId, isEditMode]);

  const fetchRepositories = async () => {
    try {
      const repos = await apiClient.getRepositories();
      setRepositories(repos);
    } catch (err) {
      console.error("Erreur lors de la récupération des repositories:", err);
    }
  };

  const fetchTicket = async () => {
    if (!ticketId) return;

    try {
      setLoadingTicket(true);
      const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Ticket non trouvé");
      }

      const ticket = await response.json();
      setFormData({
        title: ticket.title,
        description: ticket.description || "",
        priority: ticket.priority,
        type: ticket.ticket_type,
        status: ticket.status,
        repository: ticket.repository_id,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors du chargement du ticket");
    } finally {
      setLoadingTicket(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      setError("Le titre du ticket est requis");
      return;
    }

    if (!isEditMode && !formData.repository) {
      setError("Veuillez sélectionner un repository");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const url = isEditMode ? `${API_BASE_URL}/tickets/${ticketId}` : `${API_BASE_URL}/tickets";

      const method = isEditMode ? "PUT" : "POST";

      const body = isEditMode
        ? {
            title: formData.title.trim(),
            description: formData.description.trim() || null,
            priority: formData.priority,
            status: formData.status,
          }
        : {
            title: formData.title.trim(),
            description: formData.description.trim() || null,
            priority: formData.priority,
            type: formData.type,
            repository_id: formData.repository,
          };

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error(`Error ${isEditMode ? "updating" : "creating"} ticket:`, errorData);
        throw new Error(errorData.detail || `Erreur lors de ${isEditMode ? "la modification" : "la création"} du ticket`);
      }

      // Redirect to the tickets list for the repository
      if (formData.repository) {
        navigate(`/repository/${formData.repository}/tickets`);
      } else {
        navigate("/projects");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Erreur lors de ${isEditMode ? "la modification" : "la création"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  if (loadingTicket) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <AppBar />
        <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-slate-600 dark:text-slate-400">Chargement du ticket...</div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <AppBar />

      <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-slate-900">{isEditMode ? "Modifier le ticket" : "Créer un nouveau ticket"}</h2>
          <p className="text-slate-600 mt-1">{isEditMode ? "Modifiez les informations du ticket" : "Créez un ticket pour suivre une tâche"}</p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle>Informations du ticket</CardTitle>
              <CardDescription>{isEditMode ? "Modifiez les champs nécessaires" : "Remplissez les informations nécessaires"}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {!isEditMode && (
                  <div className="space-y-2">
                    <Label htmlFor="repository">Repository *</Label>
                    <select
                      id="repository"
                      name="repository"
                      value={formData.repository}
                      onChange={handleChange}
                      required
                      className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Sélectionnez un repository</option>
                      {repositories.map((repo) => (
                        <option key={repo.id} value={repo.id}>
                          {repo.name}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-slate-500">Associez ce ticket à un repository spécifique</p>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="title">Titre *</Label>
                  <Input id="title" name="title" value={formData.title} onChange={handleChange} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={6}
                    className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Décrivez le ticket en détail..."
                  />
                </div>

                {!isEditMode && (
                  <div className="space-y-2">
                    <Label htmlFor="type">Type</Label>
                    <select
                      id="type"
                      name="type"
                      value={formData.type}
                      onChange={handleChange}
                      className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="feature">Fonctionnalité</option>
                      <option value="bugfix">Correction de bug</option>
                      <option value="refactor">Refactorisation</option>
                      <option value="documentation">Documentation</option>
                    </select>
                  </div>
                )}

                {isEditMode && (
                  <div className="space-y-2">
                    <Label htmlFor="status">Statut</Label>
                    <select
                      id="status"
                      name="status"
                      value={formData.status}
                      onChange={handleChange}
                      className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="open">Ouvert</option>
                      <option value="in_progress">En cours</option>
                      <option value="pending_validation">En attente de validation</option>
                      <option value="closed">Fermé</option>
                      <option value="cancelled">Annulé</option>
                    </select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="priority">Priorité</Label>
                  <select
                    id="priority"
                    name="priority"
                    value={formData.priority}
                    onChange={handleChange}
                    className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Basse</option>
                    <option value="medium">Moyenne</option>
                    <option value="high">Haute</option>
                    <option value="critical">Critique</option>
                  </select>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      if (isEditMode && formData.repository) {
                        navigate(`/repository/${formData.repository}/tickets`);
                      } else {
                        navigate("/projects");
                      }
                    }}
                    disabled={loading}
                    className="flex-1"
                  >
                    Annuler
                  </Button>
                  <Button type="submit" disabled={loading} className="flex-1">
                    {loading ? (isEditMode ? "Modification..." : "Création...") : isEditMode ? "Modifier le ticket" : "Créer le ticket"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default CreateTicket;
