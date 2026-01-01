import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

function Projects({ token, onLogout }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");

  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError("");

      // Récupérer l'utilisateur connecté
      const userResponse = await fetch("https://api.github.com/user", {
        headers: {
          Authorization: `token ${token}`,
          Accept: "application/vnd.github.v3+json",
        },
      });

      if (!userResponse.ok) {
        throw new Error("Token invalide");
      }

      const userData = await userResponse.json();
      setUsername(userData.login);

      // Récupérer les repositories
      const reposResponse = await fetch("https://api.github.com/user/repos?sort=updated&per_page=50", {
        headers: {
          Authorization: `token ${token}`,
          Accept: "application/vnd.github.v3+json",
        },
      });

      if (!reposResponse.ok) {
        throw new Error("Erreur lors de la récupération des projets");
      }

      const reposData = await reposResponse.json();
      setProjects(reposData);
    } catch (err) {
      setError(err.message);
      if (err.message.includes("Token invalide")) {
        setTimeout(() => onLogout(), 2000);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
  };

  return (
    <div>
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>📦 Mes Projets</h1>
          <div className="nav">
            <Link to="/projects" className="nav-link active">
              Projets
            </Link>
            <Link to="/create-ticket" className="nav-link">
              Nouveau ticket
            </Link>
            <button onClick={onLogout} className="btn btn-danger" style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}>
              Déconnexion
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="container" style={{ paddingTop: "2rem" }}>
        {username && (
          <div className="message message-info mb-4">
            Connecté en tant que <strong>{username}</strong>
          </div>
        )}

        {error && <div className="message message-error">{error}</div>}

        {loading ? (
          <div className="spinner"></div>
        ) : (
          <>
            <div style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <h2 style={{ fontSize: "1.5rem", fontWeight: "700" }}>
                {projects.length} projet{projects.length > 1 ? "s" : ""}
              </h2>
              <button onClick={fetchProjects} className="btn btn-secondary" style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}>
                🔄 Actualiser
              </button>
            </div>

            {projects.length === 0 ? (
              <div className="card text-center" style={{ padding: "3rem" }}>
                <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>Aucun projet trouvé</p>
                <a href="https://github.com/new" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                  Créer un nouveau projet sur GitHub
                </a>
              </div>
            ) : (
              <div className="grid">
                {projects.map((project) => (
                  <div key={project.id} className="card">
                    <div style={{ marginBottom: "1rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "0.5rem" }}>
                        <h3 style={{ fontSize: "1.125rem", fontWeight: "600", wordBreak: "break-word" }}>{project.name}</h3>
                        {project.private ? <span className="badge badge-warning">Privé</span> : <span className="badge badge-success">Public</span>}
                      </div>
                      <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>{project.description || "Aucune description"}</p>
                    </div>

                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
                      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                        {project.language && <span>📝 {project.language}</span>}
                        <span>⭐ {project.stargazers_count}</span>
                        <span>🔀 {project.forks_count}</span>
                      </div>
                      <div style={{ marginTop: "0.5rem" }}>Mis à jour le {formatDate(project.updated_at)}</div>
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem", flexDirection: "column" }}>
                      <a href={project.html_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}>
                        Voir sur GitHub
                      </a>
                      <Link to={`/create-ticket?repo=${project.full_name}`} className="btn btn-primary" style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}>
                        Créer un ticket
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Projects;
