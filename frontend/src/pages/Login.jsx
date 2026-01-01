import { useState } from "react";

function Login({ onLogin }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!token.trim()) {
      setError("Veuillez entrer un token GitHub");
      return;
    }

    if (!token.startsWith("ghp_") && !token.startsWith("github_pat_")) {
      setError('Le token doit commencer par "ghp_" ou "github_pat_"');
      return;
    }

    setLoading(true);

    try {
      // Vérifier si le token est valide en faisant une requête à l'API GitHub
      const response = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `token ${token}`,
          Accept: "application/vnd.github.v3+json",
        },
      });

      if (!response.ok) {
        throw new Error("Token invalide ou expiré");
      }

      const userData = await response.json();
      console.log("Connecté en tant que:", userData.login);

      onLogin(token);
    } catch (err) {
      setError(err.message || "Erreur de connexion. Vérifiez votre token.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="card" style={{ maxWidth: "500px", width: "100%" }}>
        <div className="text-center mb-4">
          <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🚀 Auto-Code</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>Plateforme de gestion de développement automatisé</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="label" htmlFor="token">
              Token GitHub Personnel
            </label>
            <input id="token" type="password" className="input" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" value={token} onChange={(e) => setToken(e.target.value)} disabled={loading} />
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
              Créez un token sur{" "}
              <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" style={{ color: "var(--primary-color)" }}>
                GitHub Settings → Developer settings → Personal access tokens
              </a>
            </p>
          </div>

          {error && <div className="message message-error">{error}</div>}

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Connexion en cours..." : "Se connecter"}
          </button>
        </form>

        <div className="mt-4 text-center">
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Votre token est stocké localement dans votre navigateur</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
