import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Layout } from "./components/layout/Layout";
import { Login } from "./pages/auth/Login";
import { Dashboard } from "./pages/Dashboard";
import { Repositories } from "./pages/development/repository/Repositories";
import { RepositoryDetails } from "./pages/development/repository/RepositoryDetails";
import { Issues } from "./pages/development/issues/Issues";
import IssueDetails from "./pages/development/issues/IssueDetails";
import { Messages } from "./pages/development/messages/Messages";
import { Metamodels } from "./pages/development/metamodels/Metamodels";
import { MetamodelDetail } from "./pages/development/metamodels/MetamodelDetail";
import { MetamodelForm } from "./pages/development/metamodels/MetamodelForm";
import Profile from "./pages/profile/Profile";
import { NotFound } from "./pages/NotFound";
import { Toaster } from "@/components/ui/toaster";

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

// Authenticated Layout Wrapper
function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();

  return (
    <Layout user={user} onSignOut={signOut}>
      {children}
    </Layout>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Protected Routes with Layout */}
          <Route
            path="/development/repositories"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Repositories />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/repositories/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <RepositoryDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/repositories/:id/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <RepositoryDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/repositories/:repositoryId/issues"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Issues />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Issues />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Metamodels routes */}
          <Route
            path="/development/metamodeles"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Metamodels />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/metamodeles/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <MetamodelForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/metamodeles/:id"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <MetamodelDetail />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/metamodeles/:id/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <MetamodelForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/:issueId"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/:issueId/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/development/issues/:issueId/messages"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Messages />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Profile route */}
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Profile />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Login route - public */}
          <Route path="/login" element={<Login />} />

          {/* Dashboard - page d'accueil */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Dashboard />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* 404 - Page non trouvée */}
          <Route
            path="*"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <NotFound />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
        <Toaster />
      </AuthProvider>
    </Router>
  );
}

export default App;
