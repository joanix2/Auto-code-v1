import { AppBar } from "@/components/AppBar";
import { ProfileInformation } from "@/components/profile/ProfileInformation";
import { GitHubSync } from "@/components/profile/GitHubSync";

function Profile() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <AppBar />

      <main className="container px-4 py-8 md:px-8 max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Paramètres du Profil</h2>
          <p className="text-slate-600 dark:text-slate-400 mt-1">Gérez vos informations personnelles et vos intégrations</p>
        </div>

        {/* Profile Content */}
        <div className="space-y-6">
          <ProfileInformation />
          <GitHubSync />
        </div>
      </main>
    </div>
  );
}

export default Profile;
