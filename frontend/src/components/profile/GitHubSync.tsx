import { useAuth } from "@/contexts/AuthContext";
import { useGitHubAuth } from "@/hooks/useGitHubAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Github, CheckCircle, XCircle } from "lucide-react";

export function GitHubSync() {
  const { user } = useAuth();
  const { connectGitHub, disconnectGitHub, loading, error } = useGitHubAuth();

  const hasToken = user?.github_token && user.github_token.length > 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
            <Github className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-2xl">GitHub Integration</CardTitle>
            <CardDescription>Connect your GitHub account with OAuth2</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="rounded-lg border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-medium">Connection Status:</span>
              {hasToken ? (
                <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                  <CheckCircle className="h-4 w-4" />
                  Connected
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-slate-500">
                  <XCircle className="h-4 w-4" />
                  Not connected
                </span>
              )}
            </div>
          </div>

          {!hasToken ? (
            <div className="pt-2">
              <Button onClick={connectGitHub} disabled={loading} className="w-full bg-[#24292e] hover:bg-[#1a1e22] text-white">
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Connecting...
                  </>
                ) : (
                  <>
                    <Github className="mr-2 h-4 w-4" />
                    Connect with GitHub
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="pt-2 space-y-3">
              <p className="text-sm text-muted-foreground">Your GitHub account is connected. You can now create repositories and sync your existing ones automatically.</p>
              <Button onClick={disconnectGitHub} variant="outline" disabled={loading} className="w-full">
                {loading ? "Disconnecting..." : "Disconnect GitHub"}
              </Button>
            </div>
          )}
        </div>

        <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 p-4 space-y-2">
          <h4 className="font-medium text-blue-900 dark:text-blue-100">Why connect GitHub?</h4>
          <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
            <li>Create repositories directly on GitHub</li>
            <li>Sync your existing repositories automatically</li>
            <li>Secure OAuth2 authentication</li>
            <li>Access private repositories</li>
          </ul>
          <p className="text-xs text-blue-700 dark:text-blue-400 pt-2">OAuth provides secure access without storing passwords. You can revoke access anytime from your GitHub settings.</p>
        </div>
      </CardContent>
    </Card>
  );
}
