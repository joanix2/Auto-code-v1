import React, { useState } from "react";
import { Send, Bot, User as UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

interface GraphToolbarProps {
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onSendPrompt: () => void;
  messages?: ChatMessage[];
  className?: string;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({ prompt, onPromptChange, onSendPrompt, messages = [], className = "" }) => {
  const [focused, setFocused] = useState(false);
  const showHistory = messages.length > 0 && focused;

  return (
    <div className={cn(
      "absolute bottom-4 md:bottom-6 left-4 right-4 md:left-6 md:right-6",
      "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
      "border rounded-lg shadow-lg",
      "max-w-xl mx-auto",
      className,
    )}>
      {/* Historique */}
      {showHistory && (
        <div className="max-h-48 overflow-y-auto border-b px-4 py-2 space-y-2">
          {messages.map((msg, i) => (
            <div key={i} className={cn("flex gap-2 text-sm", msg.role === "assistant" ? "text-muted-foreground" : "")}>
              {msg.role === "user" ? (
                <UserIcon className="h-4 w-4 mt-0.5 shrink-0" />
              ) : (
                <Bot className="h-4 w-4 mt-0.5 shrink-0" />
              )}
              <span>{msg.text}</span>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex items-center gap-2 px-4 py-3">
        <Input
          type="text"
          placeholder="Demandez à l'IA de modifier le graphe..."
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 200)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSendPrompt(); } }}
          className="flex-1 h-9"
        />
        <Button onClick={onSendPrompt} variant="default" size="sm" className="shrink-0 h-9" disabled={!prompt.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
