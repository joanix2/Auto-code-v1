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
      "absolute bottom-4 md:bottom-6 left-1/2 -translate-x-1/2",
      "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
      "border rounded-t-lg md:rounded-lg shadow-lg",
      "max-w-xl w-full md:mx-4",
      className,
    )}>
      <div className="flex items-center gap-2 px-4 py-3">
        <div className="relative flex-1">
          <Input
            type="text"
            placeholder="Demandez à l'IA de modifier le graphe..."
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSendPrompt(); } }}
            className="pr-10 h-9"
          />
          <Button onClick={onSendPrompt} variant="ghost" size="icon" className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7" disabled={!prompt.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
