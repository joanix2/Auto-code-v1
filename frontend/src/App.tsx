import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Layout } from "./components/layout/Layout";
import { Login } from "./pages/auth/Login";
import { Repositories } from "./pages/repository/Repositories";
import { RepositoryDetails } from "./pages/repository/RepositoryDetails";
import { Issues } from "./pages/issues/Issues";
import IssueDetails from "./pages/issues/IssueDetails";
import { Messages } from "./pages/messages/Messages";
import Profile from "./pages/profile/Profile";
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
            path="/repositories"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Repositories />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/repositories/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <RepositoryDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/repositories/:id/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <RepositoryDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/repositories/:repositoryId/issues"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Issues />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/issues"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Issues />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/issues/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
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

          <Route
            path="/issues/:issueId"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/issues/:issueId/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <IssueDetails />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/issues/:issueId/messages"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Messages />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* Default route - redirect to repositories */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Navigate to="/repositories" replace />
              </ProtectedRoute>
            }
          />

          {/* 404 - Redirect to repositories */}
          <Route path="*" element={<Navigate to="/repositories" replace />} />
        </Routes>
        <Toaster />
      </AuthProvider>
    </Router>
  );
}

export default App;
