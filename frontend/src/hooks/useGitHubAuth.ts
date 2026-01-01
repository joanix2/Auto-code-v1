import { useState } from "react";

export function useGitHubAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connectGitHub = async () => {
    try {
      setLoading(true);
      setError(null);

      // Récupérer l'URL d'autorisation
      const response = await fetch("http://localhost:8000/api/auth/github/login", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to get GitHub authorization URL");
      }

      const data = await response.json();

      // Ouvrir une popup pour l'authentification GitHub
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;

      const popup = window.open(data.auth_url, "GitHub OAuth", `width=${width},height=${height},left=${left},top=${top}`);

      if (!popup) {
        throw new Error("Popup blocked. Please allow popups for this site.");
      }

      // Écouter le callback
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;

        if (event.data.type === "github-oauth-success") {
          popup?.close();
          window.removeEventListener("message", handleMessage);
          // Recharger pour mettre à jour le token
          window.location.reload();
        }
      };

      window.addEventListener("message", handleMessage);

      // Nettoyer si la popup est fermée manuellement
      const checkPopup = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkPopup);
          window.removeEventListener("message", handleMessage);
          setLoading(false);
        }
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub authentication failed");
      setLoading(false);
    }
  };

  const disconnectGitHub = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("http://localhost:8000/api/auth/github/disconnect", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to disconnect GitHub");
      }

      // Recharger pour mettre à jour l'état
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect GitHub");
      setLoading(false);
    }
  };

  return { connectGitHub, disconnectGitHub, loading, error };
}
