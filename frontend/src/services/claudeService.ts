/**
 * Service pour gérer l'intégration avec Claude Code via l'API backend
 */
import type { Ticket, Repository } from "@/types";

interface ClaudeResponse {
  ticket_id: string;
  ticket_title: string;
  repository: string;
  claude_response: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
  model: string;
  status_updated: boolean;
}

interface NextTicketResponse {
  ticket: Ticket | null;
  queue_position: number;
  total_open_tickets: number;
}

export class ClaudeService {
  private static API_BASE = "http://localhost:8000/api";

  /**
   * Récupère le prochain ticket dans la queue
   */
  static async getNextTicket(repositoryId: string): Promise<NextTicketResponse> {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("Non authentifié");
    }

    const response = await fetch(`${this.API_BASE}/tickets/repository/${repositoryId}/next`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erreur lors de la récupération du prochain ticket");
    }

    return response.json();
  }

  /**
   * Lance le développement d'un ticket avec Claude
   */
  static async developTicket(ticketId: string, additionalContext?: string): Promise<ClaudeResponse> {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("Non authentifié");
    }

    const response = await fetch(`${this.API_BASE}/tickets/${ticketId}/develop-with-claude`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        ticket_id: ticketId,
        additional_context: additionalContext,
        auto_update_status: true,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erreur lors de l'appel à Claude");
    }

    return response.json();
  }

  /**
   * Lance le développement du prochain ticket dans la queue
   */
  static async developNextTicket(repositoryId: string, additionalContext?: string): Promise<ClaudeResponse> {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("Non authentifié");
    }

    const response = await fetch(`${this.API_BASE}/tickets/repository/${repositoryId}/develop-next`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        additional_context: additionalContext,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erreur lors du développement automatique");
    }

    return response.json();
  }

  /**
   * Formate la réponse de Claude pour affichage
   */
  static formatResponse(response: ClaudeResponse): string {
    return `# Développement automatique

**Ticket:** ${response.ticket_title}
**Repository:** ${response.repository}
**Modèle:** ${response.model}

## 📊 Utilisation
- Tokens d'entrée: ${response.usage?.input_tokens || "N/A"}
- Tokens de sortie: ${response.usage?.output_tokens || "N/A"}

## 💡 Réponse de Claude

${response.claude_response}
`;
  }
}
