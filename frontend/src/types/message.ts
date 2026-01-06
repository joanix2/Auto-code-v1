/**
 * Message Types
 */

export type MessageAuthorType = "user" | "copilot" | "system";

export interface Message {
  id: string;
  issue_id: string;
  content: string;
  author_username: string;
  author_type: MessageAuthorType;
  created_at: string;
  updated_at?: string;
}

export interface MessageCreate {
  issue_id: string;
  content: string;
  author_username: string;
  author_type?: MessageAuthorType;
}

export interface MessageUpdate {
  content?: string;
}
