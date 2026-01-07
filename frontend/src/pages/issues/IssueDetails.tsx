import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useRepositories } from "@/hooks/useRepositories";
import { useIssues } from "@/hooks/useIssues";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import type { IssueCreate, IssueUpdate, IssuePriority, IssueType, IssueStatus } from "@/types";

interface IssueDetailsData {
  title: string;
  description: string;
  priority: IssuePriority;
  type: IssueType;
  status: IssueStatus;
  repository_id: string;
}

export function IssueDetails() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { issueId } = useParams<{ issueId?: string }>();
  const repositoryIdParam = searchParams.get("repository");

  const isEditMode = !!issueId;

  const { repositories, loading: loadingRepos } = useRepositories();
  const { getIssue, createIssue, updateIssue } = useIssues(repositoryIdParam || "");

  const [formData, setFormData] = useState<IssueDetailsData>({
    title: "",
    description: "",
    priority: "medium" as IssuePriority,
    type: "feature" as IssueType,
    status: "open" as IssueStatus,
    repository_id: repositoryIdParam || "",
  });

  const [loading, setLoading] = useState(false);
  const [loadingIssue, setLoadingIssue] = useState(isEditMode);
  const [error, setError] = useState("");

  // Load issue data for edit mode
  useEffect(() => {
    const loadIssue = async () => {
      if (!isEditMode || !issueId) return;

      try {
        setLoadingIssue(true);
        const issue = await getIssue(issueId);

        setFormData({
          title: issue.title,
          description: issue.description || "",
          priority: issue.priority,
          type: issue.issue_type,
          status: issue.status,
          repository_id: issue.repository_id,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load issue");
      } finally {
        setLoadingIssue(false);
      }
    };

    loadIssue();
  }, [issueId, isEditMode, getIssue]);

  // Set repository from URL param
  useEffect(() => {
    if (repositoryIdParam && !isEditMode) {
      setFormData((prev) => ({ ...prev, repository_id: repositoryIdParam }));
    }
  }, [repositoryIdParam, isEditMode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      setError("Title is required");
      return;
    }

    if (!isEditMode && !formData.repository_id) {
      setError("Please select a repository");
      return;
    }

    try {
      setLoading(true);
      setError("");

      if (isEditMode && issueId) {
        // Update existing issue
        const updateData: IssueUpdate = {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          priority: formData.priority,
          status: formData.status,
        };

        await updateIssue(issueId, updateData);
      } else {
        // Create new issue
        const createData: IssueCreate = {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          priority: formData.priority,
          issue_type: formData.type,
          repository_id: formData.repository_id,
        };

        await createIssue(createData);
      }

      // Redirect to issues list
      if (formData.repository_id) {
        navigate(`/repositories/${formData.repository_id}/issues`);
      } else {
        navigate("/repositories");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEditMode ? "update" : "create"} issue`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (formData.repository_id) {
      navigate(`/repositories/${formData.repository_id}/issues`);
    } else {
      navigate("/repositories");
    }
  };

  if (loadingIssue) {
    return (
      <div className="container mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <Button variant="ghost" size="sm" onClick={handleCancel} className="mb-3 sm:mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{isEditMode ? "Edit Issue" : "Create New Issue"}</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">{isEditMode ? "Update the issue information" : "Fill in the details to create a new issue"}</p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>{isEditMode ? "Issue Information" : "New Issue"}</CardTitle>
          <CardDescription>{isEditMode ? "Edit the fields you want to update" : "Provide the necessary information"}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Repository Selection (only for create mode) */}
            {!isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="repository_id">Repository *</Label>
                <Select value={formData.repository_id} onValueChange={(value) => setFormData((prev) => ({ ...prev, repository_id: value }))} disabled={loadingRepos}>
                  <SelectTrigger id="repository_id">
                    <SelectValue placeholder="Select a repository" />
                  </SelectTrigger>
                  <SelectContent>
                    {repositories.map((repo) => (
                      <SelectItem key={repo.id} value={repo.id}>
                        {repo.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">Associate this issue with a specific repository</p>
              </div>
            )}

            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input id="title" name="title" value={formData.title} onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))} placeholder="Enter issue title" required />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the issue in detail..."
                rows={6}
              />
            </div>

            {/* Type (only for create mode) */}
            {!isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select value={formData.type} onValueChange={(value) => setFormData((prev) => ({ ...prev, type: value as IssueType }))}>
                  <SelectTrigger id="type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="feature">Feature</SelectItem>
                    <SelectItem value="bug">Bug</SelectItem>
                    <SelectItem value="documentation">Documentation</SelectItem>
                    <SelectItem value="refactor">Refactor</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Status (only for edit mode) */}
            {isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={formData.status} onValueChange={(value) => setFormData((prev) => ({ ...prev, status: value as IssueStatus }))}>
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="review">Review</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Priority */}
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select value={formData.priority} onValueChange={(value) => setFormData((prev) => ({ ...prev, priority: value as IssuePriority }))}>
                <SelectTrigger id="priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={handleCancel} disabled={loading} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {isEditMode ? "Updating..." : "Creating..."}
                  </>
                ) : (
                  <>{isEditMode ? "Update Issue" : "Create Issue"}</>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default IssueDetails;
