/**
 * Message Service - API calls for messages (PR comments)
 */
import { Message, MessageCreate, MessageUpdate } from "../types";
import { BaseService } from "./base.service";
import { apiService } from "./api.service";

class MessageService extends BaseService<Message, MessageCreate, MessageUpdate> {
  protected basePath = "/api/messages";

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
}

export const messageService = new MessageService();
export default messageService;
