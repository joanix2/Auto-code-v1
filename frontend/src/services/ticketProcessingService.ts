/**
 * Service pour gérer le traitement automatique des tickets
 */
import type { Ticket, Repository } from "@/types";

interface ProcessingResponse {
  status: string;
  message: string;
  ticket_id: string;
  workflow_started: boolean;
}

interface NextTicketResponse {
  ticket: Ticket | null;
  queue_position: number;
  total_open_tickets: number;
}

export class TicketProcessingService {
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
   * Lance le traitement automatique d'un ticket (LangGraph workflow)
   */
  static async processTicket(ticketId: string): Promise<ProcessingResponse> {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("Non authentifié");
    }

    const response = await fetch(`${this.API_BASE}/tickets/processing/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        ticket_id: ticketId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erreur lors du lancement du traitement");
    }

    return response.json();
  }

  /**
   * Lance le traitement du prochain ticket dans la queue
   */
  static async processNextTicket(repositoryId: string): Promise<ProcessingResponse> {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("Non authentifié");
    }

    // D'abord récupérer le prochain ticket
    const nextTicketResponse = await this.getNextTicket(repositoryId);
    
    if (!nextTicketResponse.ticket) {
      throw new Error("Aucun ticket en attente dans la queue");
    }

    // Puis lancer son traitement
    return this.processTicket(nextTicketResponse.ticket.id);
  }

  /**
   * Soumet le résultat de validation humaine
   */
  static async submitValidation(
    ticketId: string, 
    approved: boolean, 
    feedback?: string
  ): Promise<{ success: boolean; message: string }> {
    const token = localStorage.getItem("token");
    if (!token) {
      throw new Error("Non authentifié");
    }

    const response = await fetch(`${this.API_BASE}/tickets/processing/validate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        ticket_id: ticketId,
        approved,
        feedback,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erreur lors de la validation");
    }

    return response.json();
  }
}
