import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      // Rediriger vers login avec message d'erreur
      navigate("/login?error=GitHub authentication failed");
      return;
    }

    if (token) {
      // Stocker le token
      localStorage.setItem("token", token);

      // Rafraîchir les données utilisateur
      refreshUser().then(() => {
        // Notifier la fenêtre parente si c'est une popup
        if (window.opener) {
          window.opener.postMessage({ type: "github-oauth-success" }, window.location.origin);
          window.close();
        } else {
          // Rediriger vers les projets
          navigate("/projects");
        }
      });
    } else {
      navigate("/login");
    }
  }, [searchParams, navigate, refreshUser]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-slate-600 dark:text-slate-400">Connexion en cours...</p>
      </div>
    </div>
  );
}
