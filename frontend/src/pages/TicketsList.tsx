import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, TouchSensor, useSensor, useSensors, DragEndEvent } from "@dnd-kit/core";
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppBar } from "@/components/AppBar";
import { Input } from "@/components/ui/input";
import { SortableTicketCard } from "@/components/SortableTicketCard";
import { DeleteTicketDialog } from "@/components/DeleteTicketDialog";
import { DevelopmentBanner } from "@/components/DevelopmentBanner";
import { TicketStatusFilter } from "@/components/TicketStatusFilter";
import type { Ticket, Repository } from "@/types";
import { TicketStatus } from "@/types";

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
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ticketToDelete, setTicketToDelete] = useState<Ticket | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [developing, setDeveloping] = useState(false);
  const [claudeResponse, setClaudeResponse] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200,
        tolerance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

      // Les tickets sont déjà triés par ordre dans le backend
      setTickets(ticketsData);
      setFilteredTickets(ticketsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la récupération des tickets");
    } finally {
      setLoading(false);
    }
  }, [repositoryId]);

  // Filtrage avec distance de Levenshtein et statut
  useEffect(() => {
    let filtered = tickets;

    // Filtrer par statut
    if (statusFilter !== "all") {
      filtered = filtered.filter((ticket) => ticket.status === statusFilter);
    }

    // Filtrer par recherche
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const threshold = 3;

      filtered = filtered
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
    }

    setFilteredTickets(filtered);
  }, [searchQuery, statusFilter, tickets]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const handleEdit = (ticketId: string) => {
    navigate(`/ticket/${ticketId}/edit`);
  };

  const handleDelete = (ticketId: string) => {
    const ticket = tickets.find((t) => t.id === ticketId);
    if (ticket) {
      setTicketToDelete(ticket);
      setDeleteDialogOpen(true);
    }
  };

  const confirmDelete = async () => {
    if (!ticketToDelete) return;

    try {
      setDeleting(true);
      const response = await fetch(`http://localhost:8000/api/tickets/${ticketToDelete.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la suppression du ticket");
      }

      // Close dialog and refresh tickets list
      setDeleteDialogOpen(false);
      setTicketToDelete(null);
      fetchTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la suppression");
    } finally {
      setDeleting(false);
    }
  };

  const handleDevelop = async (ticketId: string) => {
    try {
      setDeveloping(true);
      setError("");
      setClaudeResponse(null);

      const response = await fetch(`http://localhost:8000/api/tickets/${ticketId}/develop-with-opencode`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          additional_context: "",
          auto_update_status: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erreur lors du développement automatique");
      }

      const result = await response.json();

      // Rafraîchir la liste des tickets
      fetchTickets();

      // Notification de succès
      alert(`✅ Développement terminé avec succès!\n\nRepository: ${result.repository}\nChemin: ${result.repository_path}\n\nStatut mis à jour: ${result.status_updated ? "Oui" : "Non"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors du développement automatique");
    } finally {
      setDeveloping(false);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = filteredTickets.findIndex((ticket) => ticket.id === active.id);
    const newIndex = filteredTickets.findIndex((ticket) => ticket.id === over.id);

    if (oldIndex !== -1 && newIndex !== -1) {
      const newTickets = arrayMove(filteredTickets, oldIndex, newIndex);
      setFilteredTickets(newTickets);

      // Update the order on the backend
      try {
        const updates = newTickets.map((ticket, index) => ({
          ticket_id: ticket.id,
          order: index,
        }));

        const response = await fetch("http://localhost:8000/api/tickets/reorder", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ updates }),
        });

        if (!response.ok) {
          throw new Error("Erreur lors de la mise à jour de l'ordre");
        }

        // Refresh to get updated data
        fetchTickets();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur lors de la réorganisation");
        // Revert on error
        setFilteredTickets(filteredTickets);
      }
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

          {/* Development Banner - Au dessus de la barre de recherche */}
          <DevelopmentBanner tickets={tickets} developing={developing} onDevelop={handleDevelop} />

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

          {/* Status Filter Bar */}
          <TicketStatusFilter
            selectedStatus={statusFilter}
            onStatusChange={setStatusFilter}
            statusCounts={{
              all: tickets.length,
              [TicketStatus.OPEN]: tickets.filter((t) => t.status === TicketStatus.OPEN).length,
              [TicketStatus.IN_PROGRESS]: tickets.filter((t) => t.status === TicketStatus.IN_PROGRESS).length,
              [TicketStatus.PENDING_VALIDATION]: tickets.filter((t) => t.status === TicketStatus.PENDING_VALIDATION).length,
              [TicketStatus.CLOSED]: tickets.filter((t) => t.status === TicketStatus.CLOSED).length,
              [TicketStatus.CANCELLED]: tickets.filter((t) => t.status === TicketStatus.CANCELLED).length,
            }}
          />
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
          <>
            {/* Développement en cours indicator */}
            {developing && (
              <Alert className="mb-6 bg-purple-50 border-purple-200 dark:bg-purple-950/20 dark:border-purple-800">
                <AlertDescription className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="font-medium text-purple-900 dark:text-purple-100">Claude est en train de développer le ticket...</span>
                </AlertDescription>
              </Alert>
            )}

            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={filteredTickets.map((ticket) => ticket.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-3">
                  {filteredTickets.map((ticket) => (
                    <SortableTicketCard key={ticket.id} ticket={ticket} onEdit={handleEdit} onDelete={handleDelete} />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <DeleteTicketDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen} ticket={ticketToDelete} onConfirm={confirmDelete} loading={deleting} />
    </div>
  );
}

export default TicketsList;
