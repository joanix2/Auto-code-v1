import React from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface GraphToolbarProps {
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onSendPrompt: () => void;
  className?: string;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({ prompt, onPromptChange, onSendPrompt, className = "" }) => {
  return (
    <div className={cn(
      "absolute bottom-4 md:bottom-6 left-4 right-4 md:left-6 md:right-6",
      "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
      "border rounded-lg shadow-lg",
      "max-w-xl mx-auto",
      className,
    )}>
      <div className="flex items-center gap-2 px-4 py-3">
        <Input
          type="text"
          placeholder="Demandez à l'IA de modifier le graphe..."
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
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
