/**
 * Message Service - API calls for messages (PR comments)
 */
import { Message, MessageCreate, MessageUpdate } from "../types";
import { apiService } from "./api.service";

class MessageService {
  private basePath = "/api/messages";

  /**
   * Get all messages for an issue
   */
  async getByIssue(issueId: string): Promise<Message[]> {
    return apiService.get<Message[]>(`${this.basePath}/issue/${issueId}`);
  }

  /**
   * Get Copilot messages for an issue
   */
  async getCopilotMessages(issueId: string): Promise<Message[]> {
    const messages = await this.getByIssue(issueId);
    return messages.filter((msg) => msg.author_type === "copilot");
  }

  /**
   * Create a new message
   */
  async create(data: MessageCreate): Promise<Message> {
    return apiService.post<Message>(this.basePath, data);
  }

  /**
   * Update a message
   */
  async update(id: string, data: MessageUpdate): Promise<Message> {
    return apiService.patch<Message>(`${this.basePath}/${id}`, data);
  }

  /**
   * Delete a message
   */
  async delete(id: string): Promise<void> {
    return apiService.delete<void>(`${this.basePath}/${id}`);
  }
}

export const messageService = new MessageService();
export default messageService;
