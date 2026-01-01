import { useState, useEffect, ChangeEvent, FormEvent } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services";
import type { Repository } from "../types";

function CreateTicket() {
  const { signOut } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    repository: searchParams.get("repo") || "",
    priority: "medium",
    type: "feature",
  });

  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchRepositories();
  }, []);

  const fetchRepositories = async () => {
    try {
      setLoadingRepos(true);
      const repos = await apiClient.getRepositories();
      setRepos(repos);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erreur lors du chargement des repositories";
      setError(errorMessage);
    } finally {
      setLoadingRepos(false);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // Validation
    if (!formData.title.trim()) {
      setError("Le titre est obligatoire");
      return;
    }

    if (!formData.description.trim()) {
      setError("La description est obligatoire");
      return;
    }

    if (!formData.repository) {
      setError("Veuillez sélectionner un repository");
      return;
    }

    setLoading(true);

    try {
      const ticketData = {
        title: formData.title,
        description: formData.description,
        repository_id: formData.repository,
        priority: formData.priority,
        ticket_type: formData.type,
        status: "open",
      };

      const response = await apiClient.createTicket(ticketData);

      if (response) {
        setSuccess("✅ Ticket créé avec succès ! Il sera traité par l'agent AI.");

        // Réinitialiser le formulaire
        setFormData({
          title: "",
          description: "",
          repository: searchParams.get("repo") || "",
          priority: "medium",
          type: "feature",
        });

        // Rediriger après 2 secondes
        setTimeout(() => {
          navigate("/projects");
        }, 2000);
      }
    } catch (err) {
      console.error("Erreur:", err);
      const errorMessage = err instanceof Error ? err.message : "Erreur lors de la création du ticket. Vérifiez que le backend est démarré.";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>✨ Nouveau Ticket</h1>
          <div className="nav">
            <Link to="/projects" className="nav-link">
              Projets
            </Link>
            <Link to="/create-ticket" className="nav-link active">
              Nouveau ticket
            </Link>
            <button onClick={signOut} className="btn btn-danger" style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}>
              Déconnexion
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="container" style={{ paddingTop: "2rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div className="card">
            <h2 style={{ fontSize: "1.5rem", fontWeight: "700", marginBottom: "1.5rem" }}>Créer une nouvelle tâche de développement</h2>

            {error && <div className="message message-error">{error}</div>}

            {success && <div className="message message-success">{success}</div>}

            <form onSubmit={handleSubmit}>
              {/* Repository */}
              <div className="form-group">
                <label className="label" htmlFor="repository">
                  Repository GitHub *
                </label>
                <select id="repository" name="repository" className="input" value={formData.repository} onChange={handleChange} disabled={loading || loadingRepos} required>
                  <option value="">Sélectionner un repository</option>
                  {repos.map((repo) => (
                    <option key={repo.id} value={repo.name}>
                      {repo.name} {repo.description || ""}
                    </option>
                  ))}
                </select>
              </div>

              {/* Type */}
              <div className="form-group">
                <label className="label" htmlFor="type">
                  Type de tâche *
                </label>
                <select id="type" name="type" className="input" value={formData.type} onChange={handleChange} disabled={loading} required>
                  <option value="feature">✨ Nouvelle fonctionnalité</option>
                  <option value="bug">🐛 Correction de bug</option>
                  <option value="refactor">♻️ Refactoring</option>
                  <option value="docs">📝 Documentation</option>
                  <option value="test">🧪 Tests</option>
                  <option value="chore">🔧 Maintenance</option>
                </select>
              </div>

              {/* Priority */}
              <div className="form-group">
                <label className="label" htmlFor="priority">
                  Priorité *
                </label>
                <select id="priority" name="priority" className="input" value={formData.priority} onChange={handleChange} disabled={loading} required>
                  <option value="low">🟢 Basse</option>
                  <option value="medium">🟡 Moyenne</option>
                  <option value="high">🟠 Haute</option>
                  <option value="urgent">🔴 Urgente</option>
                </select>
              </div>

              {/* Title */}
              <div className="form-group">
                <label className="label" htmlFor="title">
                  Titre de la tâche *
                </label>
                <input
                  id="title"
                  name="title"
                  type="text"
                  className="input"
                  placeholder="Ex: Ajouter l'authentification utilisateur"
                  value={formData.title}
                  onChange={handleChange}
                  disabled={loading}
                  required
                />
              </div>

              {/* Description */}
              <div className="form-group">
                <label className="label" htmlFor="description">
                  Description détaillée *
                </label>
                <textarea
                  id="description"
                  name="description"
                  className="input"
                  placeholder="Décrivez en détail ce qui doit être fait, les contraintes, les exigences techniques, etc."
                  value={formData.description}
                  onChange={handleChange}
                  disabled={loading}
                  required
                  rows={6}
                />
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>💡 Plus votre description est détaillée, meilleur sera le résultat de l'agent AI</p>
              </div>

              {/* Buttons */}
              <div style={{ display: "flex", gap: "1rem", flexDirection: "column" }}>
                <button type="submit" className="btn btn-primary" disabled={loading || loadingRepos}>
                  {loading ? "⏳ Création en cours..." : "🚀 Créer le ticket"}
                </button>

                <Link to="/projects" className="btn btn-secondary" style={{ textAlign: "center" }}>
                  Annuler
                </Link>
              </div>
            </form>
          </div>

          {/* Info box */}
          <div className="message message-info mt-4">
            <strong>ℹ️ Comment ça marche ?</strong>
            <ul style={{ marginTop: "0.5rem", marginLeft: "1.25rem", fontSize: "0.875rem" }}>
              <li>Votre ticket sera ajouté à la file d'attente de traitement</li>
              <li>Un agent AI analysera votre demande et générera le code nécessaire</li>
              <li>Le code sera commit sur une nouvelle branche de votre repository</li>
              <li>Une pull request sera créée automatiquement pour review</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CreateTicket;
