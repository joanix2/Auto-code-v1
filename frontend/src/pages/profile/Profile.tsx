import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { User, Github, CheckCircle, XCircle } from "lucide-react";
import { API_URL } from "@/config/env";

function Profile() {
  const { user, refreshUser } = useAuth();
  const [githubToken, setGithubToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const getInitials = (username: string) => {
    return username.slice(0, 2).toUpperCase();
  };

  const getProfilePictureUrl = () => {
    if (user?.avatar_url) {
      if (user.avatar_url.startsWith("http://") || user.avatar_url.startsWith("https://")) {
        return user.avatar_url;
      }
      return `/assets/${user.avatar_url}?t=${Date.now()}`;
    }
    return undefined;
  };

  const handleSaveGithubToken = async () => {
    if (!githubToken.trim()) {
      setMessage({ type: "error", text: "Please enter a GitHub token" });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ github_token: githubToken }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to save GitHub token");
      }

      await refreshUser();
      setMessage({ type: "success", text: "GitHub token saved successfully!" });
      setGithubToken("");
    } catch (error) {
      setMessage({
        type: "error",
        text: error instanceof Error ? error.message : "Failed to save GitHub token",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnectGithub = async () => {
    if (!confirm("Are you sure you want to disconnect your GitHub account?")) {
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ github_token: null }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to disconnect GitHub");
      }

      await refreshUser();
      setMessage({ type: "success", text: "GitHub account disconnected successfully!" });
    } catch (error) {
      setMessage({
        type: "error",
        text: error instanceof Error ? error.message : "Failed to disconnect GitHub",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-4xl px-3 sm:px-4 py-4 sm:py-8">
      {/* Page Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Profile Settings</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">Manage your personal information and integrations</p>
      </div>

      {/* Message Alert */}
      {message && (
        <Alert variant={message.type === "error" ? "destructive" : "default"} className="mb-4">
          {message.type === "success" ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-4 sm:space-y-6">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile Information
            </CardTitle>
            <CardDescription>Your personal account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16 sm:h-20 sm:w-20">
                <AvatarImage src={getProfilePictureUrl()} alt={user?.username} />
                <AvatarFallback className="bg-gradient-to-br from-primary to-purple-600 text-white text-lg">{user?.username ? getInitials(user.username) : "U"}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-lg font-semibold">{user?.username}</h3>
                <p className="text-sm text-gray-500">{user?.email || "No email provided"}</p>
              </div>
            </div>

            <div className="grid gap-4">
              <div>
                <Label>Username</Label>
                <Input value={user?.username || ""} disabled className="bg-gray-50" />
              </div>
              <div>
                <Label>Email</Label>
                <Input value={user?.email || "Not set"} disabled className="bg-gray-50" />
              </div>
              <div>
                <Label>Account Status</Label>
                <div className="flex items-center gap-2 mt-2">
                  {user?.is_active ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm text-green-600">Active</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 text-red-600" />
                      <span className="text-sm text-red-600">Inactive</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* GitHub Integration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Github className="h-5 w-5" />
              GitHub Integration
            </CardTitle>
            <CardDescription>Connect your GitHub account to sync repositories and issues</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Github className="h-5 w-5 text-gray-600" />
                <div>
                  <p className="font-medium text-sm">GitHub Status</p>
                  <p className="text-xs text-gray-500">{user?.github_token ? "Connected" : "Not connected"}</p>
                </div>
              </div>
              {user?.github_token ? (
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-sm text-green-600 font-medium">Connected</span>
                </div>
              ) : (
                <XCircle className="h-5 w-5 text-gray-400" />
              )}
            </div>

            {user?.github_token ? (
              <div className="space-y-3">
                <Alert>
                  <AlertDescription>Your GitHub account is connected. You can now sync repositories and issues.</AlertDescription>
                </Alert>
                <Button variant="destructive" onClick={handleDisconnectGithub} disabled={loading} className="w-full sm:w-auto">
                  Disconnect GitHub
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <Alert>
                  <AlertDescription>
                    Generate a GitHub Personal Access Token with <code className="bg-gray-200 px-1 rounded">repo</code> scope and paste it below.
                  </AlertDescription>
                </Alert>
                <div className="space-y-2">
                  <Label htmlFor="github-token">GitHub Personal Access Token</Label>
                  <Input id="github-token" type="password" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" value={githubToken} onChange={(e) => setGithubToken(e.target.value)} disabled={loading} />
                  <p className="text-xs text-gray-500">
                    <a href="https://github.com/settings/tokens/new?scopes=repo" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                      Generate a new token on GitHub
                    </a>
                  </p>
                </div>
                <Button onClick={handleSaveGithubToken} disabled={loading || !githubToken.trim()} className="w-full sm:w-auto">
                  {loading ? "Saving..." : "Save GitHub Token"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Profile;
