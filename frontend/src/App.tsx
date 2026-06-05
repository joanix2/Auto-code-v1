import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Layout } from "./components/layout/Layout";
import { Login } from "./pages/auth/Login";
import { Dashboard } from "./pages/Dashboard";
import { Repositories } from "./pages/development/repository/Repositories";
import { RepositoryDetails } from "./pages/development/repository/RepositoryDetails";
import { Issues } from "./pages/development/issues/Issues";
import IssueDetails from "./pages/development/issues/IssueDetails";
import { Messages } from "./pages/development/messages/Messages";
import { DSLGraphs } from "./pages/development/dsls/DSLGraphs";
import { DSLDetails } from "./pages/development/dsls/DSLDetails";
import { DSLForm } from "./pages/development/dsls/DSLForm";
import { Projects } from "./pages/development/projects/Projects";
import { ProjectDetails } from "./pages/development/projects/ProjectDetails";
import { ProjectForm } from "./pages/development/projects/ProjectForm";
import { ProjectDetailLayout } from "./components/layout/ProjectDetailLayout";
import { FullPageLayout } from "./components/layout/FullPageLayout";
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

// Project Detail Wrapper (no sidebar, tabs in header/bottom nav)
function ProjectDetailPageWrapper({ children }: { children: React.ReactNode }) {
  const { projectId } = useParams<{ projectId: string }>();
  const { user, signOut } = useAuth();

  return (
    <ProjectDetailLayout projectId={projectId || ""} user={user} onSignOut={signOut}>
      {children}
    </ProjectDetailLayout>
  );
}

function DSLDetailPageWrapper({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const { user, signOut } = useAuth();
  const [title, setTitle] = React.useState("");

  React.useEffect(() => {
    if (!id) return;
    import("@/services/dslService").then(({ dslService }) => {
      dslService.getById(id).then((dsl) => setTitle(dsl.name)).catch(() => {});
    });
  }, [id]);

  return (
    <FullPageLayout title={title} backUrl="/development/dsls" hideHeader user={user} onSignOut={signOut}>
      {children}
    </FullPageLayout>
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

          {/* Projects routes */}
          <Route
            path="/development/projets"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <Projects />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/projets/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <ProjectForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/projets/:projectId"
            element={
              <ProtectedRoute>
                <ProjectDetailPageWrapper>
                  <ProjectDetails />
                </ProjectDetailPageWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/projets/:projectId/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <ProjectForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />

          {/* DSL routes */}
          <Route
            path="/development/dsls"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <DSLGraphs />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/dsls/new"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <DSLForm />
                </AuthenticatedLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/dsls/:id"
            element={
              <ProtectedRoute>
                <DSLDetailPageWrapper>
                  <DSLDetails />
                </DSLDetailPageWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/development/dsls/:id/edit"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout>
                  <DSLForm />
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
