import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Form, FormProps } from "@/components/common/Form/Form";
import { TextField } from "@/components/common/Form/Fields/TextField";
import { TextAreaField } from "@/components/common/Form/Fields/TextAreaField";
import { useAuth } from "@/contexts/AuthContext";
import { useRepositories } from "@/hooks/useRepositories";
import { useIssues } from "@/hooks/useIssues";
import type { IssueCreate, IssueUpdate, IssuePriority, IssueType, IssueStatus } from "@/types";

interface IssueFormData {
  title: string;
  description: string;
  priority: IssuePriority;
  type: IssueType;
  status: IssueStatus;
  repository_id: string;
}

interface IssueFormComponentProps {
  repositories: Array<{ id: string; name: string }>;
}

class IssueFormComponent extends Form<IssueFormData> {
  declare props: FormProps<IssueFormData> & IssueFormComponentProps;

  protected validate(data: IssueFormData): Record<string, string> {
    const errors: Record<string, string> = {};
    if (!data.title.trim()) errors.title = "Title is required";
    if (!this.props.isCreation && !data.repository_id) errors.repository_id = "Please select a repository";
    return errors;
  }

  protected renderActions() {
    const { isSubmitting } = this.state;
    const isEditMode = !this.props.isCreation;

    return (
      <div className="flex gap-3 pt-4">
        <button type="button" onClick={this.handleCancel} disabled={isSubmitting} className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
          Cancel
        </button>
        <button type="submit" disabled={isSubmitting} className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50">
          {isSubmitting ? (
            <>{isEditMode ? "Updating..." : "Creating..."}</>
          ) : (
            <>{isEditMode ? "Update Issue" : "Create Issue"}</>
          )}
        </button>
      </div>
    );
  }

  protected renderFields(): React.ReactNode {
    const { data, errors } = this.state;
    const isEditMode = !this.props.isCreation;

    return (
      <>
        <Card>
          <CardHeader>
            <CardTitle>{isEditMode ? "Issue Information" : "New Issue"}</CardTitle>
            <CardDescription>{isEditMode ? "Edit the fields you want to update" : "Provide the necessary information"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Title */}
            <TextField
              name="title"
              label="Title"
              value={data.title || ""}
              onChange={this.handleFieldChange}
              edit={true}
              required
              placeholder="Enter issue title"
              error={errors.title}
            />

            {/* Description */}
            <TextAreaField
              name="description"
              label="Description"
              value={data.description || ""}
              onChange={this.handleFieldChange}
              edit={true}
              placeholder="Describe the issue in detail..."
              rows={6}
              error={errors.description}
            />

            {/* Repository (only create mode) */}
            {!isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="repository_id">Repository *</Label>
                <Select value={data.repository_id} onValueChange={(v) => this.handleFieldChange("repository_id", v)}>
                  <SelectTrigger id="repository_id">
                    <SelectValue placeholder="Select a repository" />
                  </SelectTrigger>
                  <SelectContent>
                    {this.props.repositories?.map((repo: { id: string; name: string }) => (
                      <SelectItem key={repo.id} value={repo.id}>
                        {repo.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.repository_id && <p className="text-sm text-red-600">{errors.repository_id}</p>}
              </div>
            )}

            {/* Type (only create mode) */}
            {!isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select value={data.type} onValueChange={(v) => this.handleFieldChange("type", v)}>
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

            {/* Status (only edit mode) */}
            {isEditMode && (
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={data.status} onValueChange={(v) => this.handleFieldChange("status", v)}>
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
              <Select value={data.priority} onValueChange={(v) => this.handleFieldChange("priority", v)}>
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
          </CardContent>
        </Card>
      </>
    );
  }
}

export function IssueDetails() {
  const navigate = useNavigate();
  const { issueId } = useParams<{ issueId?: string }>();
  const [searchParams] = useSearchParams();
  const repositoryIdParam = searchParams.get("repository");
  const isEditMode = !!issueId;

  const { repositories, loading: loadingRepos } = useRepositories();
  const { getIssue, createIssue, updateIssue } = useIssues(repositoryIdParam || "");

  const [loadingEntity, setLoadingEntity] = useState(isEditMode);
  const [initialData, setInitialData] = useState<IssueFormData | undefined>();
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isEditMode || !issueId) {
      setLoadingEntity(false);
      return;
    }
    getIssue(issueId)
      .then((issue) => {
        setInitialData({
          title: issue.title,
          description: issue.description || "",
          priority: issue.priority,
          type: issue.issue_type,
          status: issue.status,
          repository_id: issue.repository_id,
        });
      })
      .catch((err) => {
        setError(err?.message || "Error loading issue");
      })
      .finally(() => setLoadingEntity(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditMode, issueId]);

  useEffect(() => {
    if (repositoryIdParam && !isEditMode && initialData && !initialData.repository_id) {
      setInitialData((prev) => (prev ? { ...prev, repository_id: repositoryIdParam } : prev));
    }
  }, [repositoryIdParam, isEditMode, initialData]);

  const handleSubmit = async (data: IssueFormData) => {
    try {
      if (isEditMode && issueId) {
        const updateData: IssueUpdate = {
          title: data.title.trim(),
          description: data.description.trim() || undefined,
          priority: data.priority,
          status: data.status,
        };
        await updateIssue(issueId, updateData);
      } else {
        const createData: IssueCreate = {
          title: data.title.trim(),
          description: data.description.trim() || undefined,
          priority: data.priority,
          issue_type: data.type,
          repository_id: data.repository_id,
        };
        await createIssue(createData);
      }
      navigate(data.repository_id ? `/development/repositories/${data.repository_id}/issues` : "/development/repositories");
    } catch (err) {
      setError(err?.message || `Error during ${isEditMode ? "update" : "creation"}`);
    }
  };

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
      <div className="mb-4 sm:mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(isEditMode ? `/development/issues/${issueId}` : "/development/issues")} className="mb-3 sm:mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{isEditMode ? "Edit Issue" : "Create New Issue"}</h1>
        <p className="mt-1 sm:mt-2 text-sm text-gray-600">{isEditMode ? "Update the issue information" : "Fill in the details to create a new issue"}</p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <IssueFormComponent
        initialData={initialData}
        edit={true}
        isCreation={!isEditMode}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/development/issues")}
        repositories={repositories}
      />
    </div>
  );
}

export default IssueDetails;
