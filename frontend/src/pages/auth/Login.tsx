import React, { useEffect, useState } from "react";
import { Navigate, useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";

export function Login() {
  const { isAuthenticated, loading, refreshUser } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);

  // Handle OAuth callback with token
  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      toast({
        title: "Authentication failed",
        description: error,
        variant: "destructive",
      });
      setIsProcessing(false);
      return;
    }

    if (token) {
      setIsProcessing(true);
      localStorage.setItem("token", token);

      // Refresh user data from token
      refreshUser().then(() => {
        toast({
          title: "Successfully authenticated",
          description: "Redirecting to dashboard...",
        });
        navigate("/", { replace: true });
      });
    }
  }, [searchParams, toast, navigate, refreshUser]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleGitHubLogin = () => {
    // Redirect to GitHub OAuth endpoint
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    window.location.href = `${apiUrl}/api/auth/github/login`;
  };

  if (loading || isProcessing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <img src="/logo_ticket_code.svg" alt="AutoCode Logo" className="h-16 w-16" />
          </div>
          <CardTitle className="text-2xl text-center">Welcome to AutoCode</CardTitle>
          <CardDescription className="text-center">Sign in to your account to continue</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button onClick={handleGitHubLogin} variant="outline" className="w-full" size="lg">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.840 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.430.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            Continue with GitHub
          </Button>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">AutoCode Platform v2.0</p>
        </CardFooter>
      </Card>
    </div>
  );
}
