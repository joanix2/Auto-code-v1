import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
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
import { useBaseDetails } from "../common/BaseDetailsPage";

interface IssueFormData {
  title: string;
  description: string;
  priority: IssuePriority;
  type: IssueType;
  status: IssueStatus;
  repository_id: string;
}

export function IssueDetails() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const repositoryIdParam = searchParams.get("repository");

  const { repositories, loading: loadingRepos } = useRepositories();
  const { getIssue, createIssue, updateIssue } = useIssues(repositoryIdParam || "");

  const {
    formData,
    loading,
    loadingEntity,
    error,
    isEditMode,
    setFormData,
    setError,
    handleSubmit,
    handleCancel,
    updateFormData,
  } = useBaseDetails<IssueFormData>(
    "issueId",
    {
      title: "",
      description: "",
      priority: "medium" as IssuePriority,
      type: "feature" as IssueType,
      status: "open" as IssueStatus,
      repository_id: repositoryIdParam || "",
    },
    {
      onLoadEntity: async (id: string) => {
        const issue = await getIssue(id);
        return {
          title: issue.title,
          description: issue.description || "",
          priority: issue.priority,
          type: issue.issue_type,
          status: issue.status,
          repository_id: issue.repository_id,
        };
      },
      onCreateEntity: async (data: IssueFormData) => {
        const createData: IssueCreate = {
          title: data.title.trim(),
          description: data.description.trim() || undefined,
          priority: data.priority,
          issue_type: data.type,
          repository_id: data.repository_id,
        };
        await createIssue(createData);
      },
      onUpdateEntity: async (id: string, data: IssueFormData) => {
        const updateData: IssueUpdate = {
          title: data.title.trim(),
          description: data.description.trim() || undefined,
          priority: data.priority,
          status: data.status,
        };
        await updateIssue(id, updateData);
      },
      validateForm: (data: IssueFormData, isEdit: boolean) => {
        if (!data.title.trim()) return "Title is required";
        if (!isEdit && !data.repository_id) return "Please select a repository";
        return null;
      },
      getSuccessPath: (data: IssueFormData) => {
        return data.repository_id ? `/repositories/${data.repository_id}/issues` : "/repositories";
      },
      defaultSuccessPath: "/repositories",
    }
  );

  // Set repository from URL param
  useEffect(() => {
    if (repositoryIdParam && !isEditMode) {
      setFormData((prev) => ({ ...prev, repository_id: repositoryIdParam }));
    }
  }, [repositoryIdParam, isEditMode, setFormData]);

  if (loadingEntity) {
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
                <Select value={formData.repository_id} onValueChange={(value) => updateFormData({ repository_id: value })} disabled={loadingRepos}>
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
              <Input id="title" name="title" value={formData.title} onChange={(e) => updateFormData({ title: e.target.value })} placeholder="Enter issue title" required />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={(e) => updateFormData({ description: e.target.value })}
                placeholder="Describe the issue in detail..."
                rows={6}
              />
            </div>

            {/* Type (only for create mode) */}
            {!isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select value={formData.type} onValueChange={(value) => updateFormData({ type: value as IssueType })}>
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
                <Select value={formData.status} onValueChange={(value) => updateFormData({ status: value as IssueStatus })}>
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
              <Select value={formData.priority} onValueChange={(value) => updateFormData({ priority: value as IssuePriority })}>
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
