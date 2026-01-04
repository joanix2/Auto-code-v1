import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppBar } from "@/components/AppBar";

function NewRepository() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    private: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError("Le nom du repository est requis");
      return;
    }

    if (!user?.github_token) {
      setError("Veuillez configurer votre token GitHub dans les paramètres de votre profil");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${API_BASE_URL}/repositories", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "X-GitHub-Token": user.github_token,
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          description: formData.description.trim() || null,
          private: formData.private,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erreur lors de la création du repository");
      }

      // Rediriger vers la liste des projets après succès
      navigate("/projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de la création");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppBar />

      {/* Content */}
      <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
        {/* Form Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Créer un nouveau repository</h2>
          <p className="text-slate-600 dark:text-slate-400 mt-1">Remplissez les informations pour créer votre repository</p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Form Card */}
        <div className="max-w-2xl">
          <Card className="border-slate-200 dark:border-slate-800">
            <CardHeader>
              <CardTitle>Informations du repository</CardTitle>
              <CardDescription>
                Assurez-vous d'avoir configuré votre token GitHub dans votre{" "}
                <Link to="/profile" className="text-blue-600 hover:underline">
                  profil
                </Link>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Repository Name */}
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-sm font-medium">
                    Nom du repository *
                  </Label>
                  <Input id="name" name="name" type="text" placeholder="mon-super-projet" value={formData.name} onChange={handleChange} required className="w-full" />
                  <p className="text-xs text-slate-500">Choisissez un nom court et descriptif pour votre repository</p>
                </div>

                {/* Repository Description */}
                <div className="space-y-2">
                  <Label htmlFor="description" className="text-sm font-medium">
                    Description
                  </Label>
                  <textarea
                    id="description"
                    name="description"
                    placeholder="Description de votre repository..."
                    value={formData.description}
                    onChange={handleChange}
                    rows={4}
                    className="w-full px-3 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-slate-500">Décrivez brièvement votre projet (optionnel)</p>
                </div>

                {/* Private Checkbox */}
                <div className="flex items-start space-x-3 rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-slate-50 dark:bg-slate-900/50">
                  <input
                    id="private"
                    name="private"
                    type="checkbox"
                    checked={formData.private}
                    onChange={handleChange}
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <Label htmlFor="private" className="text-sm font-medium cursor-pointer">
                      Repository privé
                    </Label>
                    <p className="text-xs text-slate-500 mt-1">Les repositories privés ne sont visibles que par vous et les collaborateurs que vous choisissez</p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => navigate("/projects")} disabled={loading} className="w-1/2">
                    Annuler
                  </Button>
                  <Button type="submit" disabled={loading} className="w-1/2 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700">
                    {loading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Création...
                      </>
                    ) : (
                      <>Créer le repository</>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card className="mt-6 border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/30">
            <CardContent className="pt-6">
              <div className="flex gap-3">
                <svg className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100">À propos de la création</h3>
                  <p className="text-xs text-blue-800 dark:text-blue-300">
                    Ce formulaire créera automatiquement le repository sur GitHub avant de l'enregistrer dans la base de données. Vous pouvez également synchroniser vos repositories existants depuis
                    GitHub en utilisant le bouton "Sync GitHub" dans la liste des projets.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default NewRepository;
