import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppBar } from "@/components/AppBar";
import { Input } from "@/components/ui/input";
import type { Ticket, Repository } from "@/types";

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

function TicketsList() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [filteredTickets, setFilteredTickets] = useState<Ticket[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchTickets = useCallback(async () => {
    if (!repositoryId) return;

    try {
      setLoading(true);
      setError("");

      // Récupérer les informations du repository
      const repos = await apiClient.getRepositories();
      const repo = repos.find((r) => r.id === repositoryId);

      if (!repo) {
        setError("Repository non trouvé");
        return;
      }

      setRepository(repo);

      // Récupérer les tickets du repository
      const response = await fetch(`http://localhost:8000/api/tickets/repository/${repositoryId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la récupération des tickets");
      }

      const ticketsData = await response.json();

      // Trier par date de création (plus récent en premier)
      const sortedTickets = ticketsData.sort((a: Ticket, b: Ticket) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return dateB - dateA;
      });

      setTickets(sortedTickets);
      setFilteredTickets(sortedTickets);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la récupération des tickets");
    } finally {
      setLoading(false);
    }
  }, [repositoryId]);

  // Filtrage avec distance de Levenshtein
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredTickets(tickets);
      return;
    }

    const query = searchQuery.toLowerCase();
    const threshold = 3;

    const filtered = tickets
      .map((ticket) => {
        const titleDistance = levenshteinDistance(ticket.title, query);
        const descriptionDistance = ticket.description ? levenshteinDistance(ticket.description, query) : Infinity;

        const bestDistance = Math.min(titleDistance, descriptionDistance);

        const titleContains = ticket.title.toLowerCase().includes(query);
        const descriptionContains = ticket.description?.toLowerCase().includes(query);

        return {
          ticket,
          score: titleContains || descriptionContains ? -1 : bestDistance,
        };
      })
      .filter((item) => item.score === -1 || item.score <= threshold)
      .sort((a, b) => a.score - b.score)
      .map((item) => item.ticket);

    setFilteredTickets(filtered);
  }, [searchQuery, tickets]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "in_progress":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "closed":
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
      case "cancelled":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "text-red-600 dark:text-red-400";
      case "high":
        return "text-orange-600 dark:text-orange-400";
      case "medium":
        return "text-yellow-600 dark:text-yellow-400";
      case "low":
        return "text-green-600 dark:text-green-400";
      default:
        return "text-slate-600 dark:text-slate-400";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppBar />

      {/* Content */}
      <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col gap-4 mb-8">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="icon" onClick={() => navigate("/projects")} className="h-10 w-10">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Button>
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Tickets {repository && `- ${repository.name}`}</h2>
              <p className="text-slate-600 dark:text-slate-400 mt-1">Gérez les tickets de ce repository</p>
            </div>
          </div>

          {/* Search Bar with Add Button */}
          <div className="flex gap-3 items-center">
            <div className="relative flex-1">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <Input
                type="text"
                placeholder="Rechercher un ticket..."
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
            <Link to={`/create-ticket?repository=${repositoryId}`}>
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

        {/* Tickets List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-slate-600 dark:text-slate-400">Chargement des tickets...</div>
          </div>
        ) : tickets.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg className="h-12 w-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"
                />
              </svg>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Aucun ticket</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">Commencez par créer un nouveau ticket pour ce repository</p>
              <Link to={`/create-ticket?repository=${repositoryId}`}>
                <Button>Créer un ticket</Button>
              </Link>
            </CardContent>
          </Card>
        ) : filteredTickets.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg className="h-12 w-12 text-slate-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Aucun résultat</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">Aucun ticket ne correspond à "{searchQuery}"</p>
              <Button onClick={() => setSearchQuery("")} variant="outline">
                Effacer la recherche
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredTickets.map((ticket) => (
              <Card key={ticket.id} className="hover:shadow-lg transition-shadow duration-200 border-slate-200 dark:border-slate-800">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white truncate">{ticket.title}</h3>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(ticket.status)}`}>{ticket.status.replace("_", " ")}</span>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-3">{ticket.description}</p>
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <div className="flex items-center gap-1">
                          <svg className={`h-4 w-4 ${getPriorityColor(ticket.priority)}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span className={getPriorityColor(ticket.priority)}>{ticket.priority}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                            />
                          </svg>
                          <span>{ticket.ticket_type}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>{new Date(ticket.created_at).toLocaleDateString("fr-FR")}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        Éditer
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default TicketsList;
