import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppBar } from "@/components/AppBar";
import { Input } from "@/components/ui/input";
import { TicketCard } from "@/components/TicketCard";
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

  const handleEdit = (ticketId: string) => {
    navigate(`/ticket/${ticketId}/edit`);
  };

  const handleDelete = async (ticketId: string) => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer ce ticket ?")) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la suppression du ticket");
      }

      // Refresh tickets list
      fetchTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la suppression");
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
              <TicketCard key={ticket.id} ticket={ticket} onEdit={handleEdit} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default TicketsList;
