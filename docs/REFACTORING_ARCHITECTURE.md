# 🏗️ Architecture Refactoring - AutoCode v2

## 📋 Vue d'ensemble

Refonte complète de l'architecture pour un code plus propre, maintenable et évolutif.

### Principes

- ✅ **Separation of Concerns** - Chaque couche a une responsabilité unique
- ✅ **DRY (Don't Repeat Yourself)** - Abstraction et réutilisation
- ✅ **Single Responsibility** - Une classe/fonction = une responsabilité
- ✅ **Composition over Inheritance** - Favoriser la composition

---

## 🎯 Modèle de données simplifié

### Concept principal

```
User → Repositories → Issues → Messages (PR comments)
```

### Règle simplifiée

```
1 Issue = 1 Branch = 1 Pull Request
```

---

## 🔧 Backend Architecture

### 📂 Structure des dossiers

```
backend/
├── src/
│   ├── models/              # Modèles de données (Pydantic)
│   │   ├── __init__.py
│   │   ├── base.py         # BaseModel avec champs communs
│   │   ├── user.py         # User model
│   │   ├── repository.py   # Repository model
│   │   ├── issue.py        # Issue model (ticket)
│   │   └── message.py      # Message model (PR comment)
│   │
│   ├── repositories/        # Data Access Layer (Neo4j)
│   │   ├── __init__.py
│   │   ├── base.py         # BaseRepository avec CRUD générique
│   │   ├── user_repository.py
│   │   ├── repository_repository.py
│   │   ├── issue_repository.py
│   │   └── message_repository.py
│   │
│   ├── services/            # Business Logic
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── github_oauth_service.py
│   │   ├── github/
│   │   │   ├── __init__.py
│   │   │   ├── github_sync_service.py      # Sync repos & issues
│   │   │   └── copilot_agent_service.py    # Copilot integration
│   │   └── messaging/
│   │       ├── __init__.py
│   │       └── message_service.py          # PR comments
│   │
│   ├── controllers/         # API Endpoints (FastAPI)
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── user_controller.py
│   │   ├── repository_controller.py
│   │   ├── issue_controller.py
│   │   └── message_controller.py
│   │
│   ├── utils/               # Utilitaires
│   │   ├── __init__.py
│   │   ├── auth.py         # JWT helpers
│   │   └── validators.py   # Validation helpers
│   │
│   └── database.py          # Neo4j connection
│
├── tests/                   # Tests unitaires
│   ├── test_models.py
│   ├── test_repositories.py
│   ├── test_services.py
│   └── test_controllers.py
│
├── main.py                  # FastAPI app
└── requirements.txt
```

---

## 📊 Modèles de données (Pydantic)

### 1. BaseModel

```python
# src/models/base.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TimestampMixin(BaseModel):
    """Mixin pour les timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class BaseEntity(TimestampMixin):
    """Base pour toutes les entités"""
    id: str = Field(..., description="Unique identifier")

    class Config:
        from_attributes = True
```

### 2. User Model

```python
# src/models/user.py
from typing import Optional
from pydantic import Field, EmailStr
from .base import BaseEntity

class User(BaseEntity):
    """User model"""
    username: str = Field(..., description="GitHub username")
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    github_id: Optional[int] = None
    github_token: Optional[str] = Field(None, exclude=True)  # Jamais exposé dans l'API

class UserPublic(BaseModel):
    """Public user representation (sans token)"""
    id: str
    username: str
    email: Optional[EmailStr]
    avatar_url: Optional[str]
```

### 3. Repository Model

```python
# src/models/repository.py
from typing import Optional
from pydantic import Field
from .base import BaseEntity

class Repository(BaseEntity):
    """GitHub repository model"""
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="owner/repo")
    owner_username: str = Field(..., description="Owner username")
    description: Optional[str] = None
    github_id: Optional[int] = None
    default_branch: str = Field(default="main")
    is_private: bool = Field(default=False)

    # Stats
    open_issues_count: int = Field(default=0)

class RepositoryCreate(BaseModel):
    """Data needed to create a repository"""
    name: str
    full_name: str
    owner_username: str
    description: Optional[str] = None
    github_id: Optional[int] = None
```

### 4. Issue Model (Ticket)

```python
# src/models/issue.py
from typing import Optional, Literal
from pydantic import Field
from .base import BaseEntity

IssueStatus = Literal["open", "in_progress", "review", "closed"]
IssuePriority = Literal["low", "medium", "high", "urgent"]
IssueType = Literal["bug", "feature", "documentation", "refactor"]

class Issue(BaseEntity):
    """Issue model (1 Issue = 1 Branch = 1 PR)"""
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")

    # Relations
    repository_id: str = Field(..., description="Repository ID")
    author_username: str = Field(..., description="Author username")

    # GitHub integration
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    github_branch_name: Optional[str] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None

    # Metadata
    status: IssueStatus = Field(default="open")
    priority: IssuePriority = Field(default="medium")
    issue_type: IssueType = Field(default="feature")

    # Copilot
    assigned_to_copilot: bool = Field(default=False)
    copilot_started_at: Optional[datetime] = None

class IssueCreate(BaseModel):
    """Data needed to create an issue"""
    title: str
    description: str
    repository_id: str
    priority: IssuePriority = "medium"
    issue_type: IssueType = "feature"

class IssueUpdate(BaseModel):
    """Data for updating an issue"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
```

### 5. Message Model (PR Comment)

```python
# src/models/message.py
from typing import Optional, Literal
from pydantic import Field
from .base import BaseEntity

MessageAuthorType = Literal["user", "copilot", "system"]

class Message(BaseEntity):
    """Message model (PR comment)"""
    content: str = Field(..., description="Message content")

    # Relations
    issue_id: str = Field(..., description="Issue ID")
    author_username: Optional[str] = None
    author_type: MessageAuthorType = Field(default="user")

    # GitHub integration
    github_comment_id: Optional[int] = None
    github_comment_url: Optional[str] = None

class MessageCreate(BaseModel):
    """Data needed to create a message"""
    content: str
    issue_id: str
    author_type: MessageAuthorType = "user"
```

---

## 🗄️ Repositories (Data Access Layer)

### BaseRepository

```python
# src/repositories/base.py
from typing import TypeVar, Generic, Optional, List, Type
from pydantic import BaseModel
from abc import ABC, abstractmethod
from ..database import Neo4jConnection

T = TypeVar('T', bound=BaseModel)

class BaseRepository(ABC, Generic[T]):
    """Generic repository pattern for Neo4j"""

    def __init__(self, db: Neo4jConnection, model: Type[T], label: str):
        self.db = db
        self.model = model
        self.label = label

    async def create(self, data: dict) -> T:
        """Create a new entity"""
        query = f"""
        CREATE (n:{self.label} $props)
        RETURN n
        """
        result = await self.db.execute_query(query, {"props": data})
        node = result[0]["n"]
        return self.model(**node)

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        RETURN n
        """
        result = await self.db.execute_query(query, {"id": entity_id})
        if not result:
            return None
        return self.model(**result[0]["n"])

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        query = f"""
        MATCH (n:{self.label})
        RETURN n
        ORDER BY n.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = await self.db.execute_query(query, {"skip": skip, "limit": limit})
        return [self.model(**row["n"]) for row in result]

    async def update(self, entity_id: str, updates: dict) -> Optional[T]:
        """Update an entity"""
        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}

        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        SET n += $updates
        SET n.updated_at = datetime()
        RETURN n
        """
        result = await self.db.execute_query(query, {"id": entity_id, "updates": updates})
        if not result:
            return None
        return self.model(**result[0]["n"])

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity"""
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        DELETE n
        RETURN count(n) as deleted
        """
        result = await self.db.execute_query(query, {"id": entity_id})
        return result[0]["deleted"] > 0
```

### Example: IssueRepository

```python
# src/repositories/issue_repository.py
from typing import List, Optional
from .base import BaseRepository
from ..models.issue import Issue

class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue entities"""

    def __init__(self, db):
        super().__init__(db, Issue, "Issue")

    async def get_by_repository(self, repository_id: str, status: Optional[str] = None) -> List[Issue]:
        """Get all issues for a repository"""
        where_clause = "WHERE n.repository_id = $repository_id"
        if status:
            where_clause += " AND n.status = $status"

        query = f"""
        MATCH (n:Issue)
        {where_clause}
        RETURN n
        ORDER BY n.created_at DESC
        """
        params = {"repository_id": repository_id}
        if status:
            params["status"] = status

        result = await self.db.execute_query(query, params)
        return [self.model(**row["n"]) for row in result]

    async def link_to_github(self, issue_id: str, github_data: dict) -> Optional[Issue]:
        """Link issue to GitHub issue/PR"""
        return await self.update(issue_id, github_data)
```

---

## ⚙️ Services (Business Logic)

### GitHubSyncService

```python
# src/services/github/github_sync_service.py
from typing import List
from github import Github
import logging

from ...models.repository import Repository, RepositoryCreate
from ...models.issue import Issue, IssueCreate
from ...repositories.repository_repository import RepositoryRepository
from ...repositories.issue_repository import IssueRepository

logger = logging.getLogger(__name__)

class GitHubSyncService:
    """Service for syncing with GitHub"""

    def __init__(self, github_token: str, repo_repository: RepositoryRepository, issue_repository: IssueRepository):
        self.github = Github(github_token)
        self.repo_repository = repo_repository
        self.issue_repository = issue_repository

    async def sync_user_repositories(self, username: str) -> List[Repository]:
        """Sync all repositories for a user"""
        logger.info(f"Syncing repositories for {username}")

        gh_user = self.github.get_user(username)
        repos = []

        for gh_repo in gh_user.get_repos():
            repo_data = RepositoryCreate(
                name=gh_repo.name,
                full_name=gh_repo.full_name,
                owner_username=username,
                description=gh_repo.description,
                github_id=gh_repo.id
            )

            # Upsert: create or update
            existing = await self.repo_repository.get_by_github_id(gh_repo.id)
            if existing:
                repo = await self.repo_repository.update(existing.id, repo_data.dict())
            else:
                repo = await self.repo_repository.create(repo_data.dict())

            repos.append(repo)

        logger.info(f"Synced {len(repos)} repositories")
        return repos

    async def sync_repository_issues(self, repository_id: str) -> List[Issue]:
        """Sync all issues for a repository"""
        repo = await self.repo_repository.get_by_id(repository_id)
        if not repo:
            raise ValueError(f"Repository {repository_id} not found")

        logger.info(f"Syncing issues for {repo.full_name}")

        gh_repo = self.github.get_repo(repo.full_name)
        issues = []

        for gh_issue in gh_repo.get_issues(state="all"):
            if gh_issue.pull_request:
                continue  # Skip PRs

            issue_data = IssueCreate(
                title=gh_issue.title,
                description=gh_issue.body or "",
                repository_id=repository_id,
                priority="medium",
                issue_type="feature"
            )

            # Upsert
            existing = await self.issue_repository.get_by_github_number(repo.id, gh_issue.number)
            if existing:
                issue = await self.issue_repository.update(existing.id, issue_data.dict())
            else:
                issue = await self.issue_repository.create(issue_data.dict())
                # Link to GitHub
                await self.issue_repository.link_to_github(issue.id, {
                    "github_issue_number": gh_issue.number,
                    "github_issue_url": gh_issue.html_url
                })

            issues.append(issue)

        logger.info(f"Synced {len(issues)} issues")
        return issues
```

---

## 🎮 Controllers (API Endpoints)

### Example: IssueController

```python
# src/controllers/issue_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..models.user import User
from ..models.issue import Issue, IssueCreate, IssueUpdate
from ..repositories.issue_repository import IssueRepository
from ..services.github.copilot_agent_service import CopilotAgentService
from ..utils.auth import get_current_user
from ..database import Neo4jConnection

router = APIRouter(prefix="/api/issues", tags=["issues"])

@router.post("/", response_model=Issue)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new issue"""
    db = Neo4jConnection()
    repo = IssueRepository(db)

    data = issue_data.dict()
    data["author_username"] = current_user.username

    issue = await repo.create(data)
    return issue

@router.get("/", response_model=List[Issue])
async def list_issues(
    repository_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """List all issues"""
    db = Neo4jConnection()
    repo = IssueRepository(db)

    if repository_id:
        issues = await repo.get_by_repository(repository_id, status)
    else:
        issues = await repo.get_all(skip, limit)

    return issues

@router.get("/{issue_id}", response_model=Issue)
async def get_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get issue by ID"""
    db = Neo4jConnection()
    repo = IssueRepository(db)

    issue = await repo.get_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return issue

@router.patch("/{issue_id}", response_model=Issue)
async def update_issue(
    issue_id: str,
    updates: IssueUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an issue"""
    db = Neo4jConnection()
    repo = IssueRepository(db)

    issue = await repo.update(issue_id, updates.dict(exclude_unset=True))
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return issue

@router.post("/{issue_id}/assign-to-copilot")
async def assign_to_copilot(
    issue_id: str,
    base_branch: str = "main",
    custom_instructions: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Assign issue to Copilot Agent"""
    db = Neo4jConnection()
    issue_repo = IssueRepository(db)

    issue = await issue_repo.get_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Get GitHub token
    from ..services.auth.github_oauth_service import get_github_token_from_user
    token = await get_github_token_from_user(current_user.username)
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")

    # Assign to Copilot
    copilot_service = CopilotAgentService(token)
    result = await copilot_service.assign_issue_to_copilot(
        issue=issue,
        base_branch=base_branch,
        custom_instructions=custom_instructions
    )

    # Update issue
    await issue_repo.update(issue_id, {
        "assigned_to_copilot": True,
        "copilot_started_at": datetime.utcnow(),
        "status": "in_progress"
    })

    return result
```

---

## 🎨 Frontend Architecture

### 📂 Structure des composants

```
frontend/src/
├── components/
│   ├── common/
│   │   ├── Card/
│   │   │   ├── BaseCard.tsx              # Abstract card component
│   │   │   ├── RepositoryCard.tsx        # Concrete: Repository
│   │   │   ├── IssueCard.tsx             # Concrete: Issue
│   │   │   └── Card.module.css
│   │   │
│   │   └── CardList/
│   │       ├── BaseCardList.tsx          # Abstract list with search + sync
│   │       ├── RepositoryList.tsx        # Concrete: Repository list
│   │       ├── IssueList.tsx             # Concrete: Issue list
│   │       └── CardList.module.css
│   │
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   │
│   └── ui/                                # shadcn/ui components
│       ├── button.tsx
│       ├── input.tsx
│       ├── card.tsx
│       └── ...
│
├── pages/
│   ├── Repositories.tsx                   # Uses RepositoryList
│   ├── Issues.tsx                         # Uses IssueList
│   └── IssueDetails.tsx
│
├── services/
│   ├── api.service.ts                     # Axios client
│   ├── repository.service.ts
│   ├── issue.service.ts
│   └── message.service.ts
│
├── types/
│   ├── index.ts
│   ├── user.ts
│   ├── repository.ts
│   ├── issue.ts
│   └── message.ts
│
└── hooks/
    ├── useRepositories.ts
    ├── useIssues.ts
    └── useMessages.ts
```

---

## 🎨 Frontend Components (React + TypeScript)

### 1. BaseCard (Abstract)

```typescript
// components/common/Card/BaseCard.tsx
import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export interface BaseCardProps<T> {
  data: T;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
  onClick?: (id: string) => void;
}

export interface CardConfig {
  showEdit?: boolean;
  showDelete?: boolean;
  showFooter?: boolean;
}

export abstract class BaseCard<T extends { id: string }> extends React.Component<BaseCardProps<T>> {
  config: CardConfig = {
    showEdit: true,
    showDelete: true,
    showFooter: true,
  };

  abstract renderHeader(): React.ReactNode;
  abstract renderContent(): React.ReactNode;
  abstract renderFooter(): React.ReactNode;

  handleClick = () => {
    if (this.props.onClick) {
      this.props.onClick(this.props.data.id);
    }
  };

  handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (this.props.onEdit) {
      this.props.onEdit(this.props.data.id);
    }
  };

  handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (this.props.onDelete) {
      this.props.onDelete(this.props.data.id);
    }
  };

  render() {
    return (
      <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={this.handleClick}>
        <CardHeader>{this.renderHeader()}</CardHeader>
        <CardContent>{this.renderContent()}</CardContent>
        {this.config.showFooter && (
          <CardFooter className="flex gap-2">
            {this.renderFooter()}
            {this.config.showEdit && (
              <Button variant="outline" size="sm" onClick={this.handleEdit}>
                Edit
              </Button>
            )}
            {this.config.showDelete && (
              <Button variant="destructive" size="sm" onClick={this.handleDelete}>
                Delete
              </Button>
            )}
          </CardFooter>
        )}
      </Card>
    );
  }
}
```

### 2. RepositoryCard (Concrete)

```typescript
// components/common/Card/RepositoryCard.tsx
import React from "react";
import { BaseCard, BaseCardProps } from "./BaseCard";
import { Repository } from "@/types/repository";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GitBranch, Lock, Unlock } from "lucide-react";

interface RepositoryCardProps extends BaseCardProps<Repository> {
  onSync?: (id: string) => void;
}

export class RepositoryCard extends BaseCard<Repository> {
  declare props: RepositoryCardProps;

  renderHeader() {
    const { data } = this.props;
    return (
      <>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            {data.name}
          </CardTitle>
          {data.is_private ? <Lock className="h-4 w-4 text-gray-500" /> : <Unlock className="h-4 w-4 text-gray-500" />}
        </div>
        <CardDescription>{data.full_name}</CardDescription>
      </>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="space-y-2">
        {data.description && <p className="text-sm text-gray-600 line-clamp-2">{data.description}</p>}
        <div className="flex gap-2">
          <Badge variant="outline">{data.default_branch}</Badge>
          <Badge>{data.open_issues_count} issues</Badge>
        </div>
      </div>
    );
  }

  renderFooter() {
    return (
      <Button
        variant="secondary"
        size="sm"
        onClick={(e) => {
          e.stopPropagation();
          this.props.onSync?.(this.props.data.id);
        }}
      >
        Sync Issues
      </Button>
    );
  }
}
```

### 3. IssueCard (Concrete)

```typescript
// components/common/Card/IssueCard.tsx
import React from "react";
import { BaseCard, BaseCardProps } from "./BaseCard";
import { Issue } from "@/types/issue";
import { CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle, Clock, Sparkles } from "lucide-react";

interface IssueCardProps extends BaseCardProps<Issue> {
  onAssignToCopilot?: (id: string) => void;
}

export class IssueCard extends BaseCard<Issue> {
  declare props: IssueCardProps;

  getStatusIcon() {
    const { status } = this.props.data;
    switch (status) {
      case "open":
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
      case "in_progress":
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case "review":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "closed":
        return <CheckCircle className="h-5 w-5 text-gray-500" />;
    }
  }

  getStatusColor() {
    const { status } = this.props.data;
    const colors = {
      open: "bg-blue-100 text-blue-800",
      in_progress: "bg-yellow-100 text-yellow-800",
      review: "bg-green-100 text-green-800",
      closed: "bg-gray-100 text-gray-800",
    };
    return colors[status];
  }

  getPriorityColor() {
    const { priority } = this.props.data;
    const colors = {
      low: "bg-gray-100 text-gray-800",
      medium: "bg-blue-100 text-blue-800",
      high: "bg-orange-100 text-orange-800",
      urgent: "bg-red-100 text-red-800",
    };
    return colors[priority];
  }

  renderHeader() {
    const { data } = this.props;
    return (
      <>
        <div className="flex items-center gap-2">
          {this.getStatusIcon()}
          <CardTitle className="flex-1">{data.title}</CardTitle>
          {data.github_issue_number && <span className="text-sm text-gray-500">#{data.github_issue_number}</span>}
        </div>
      </>
    );
  }

  renderContent() {
    const { data } = this.props;
    return (
      <div className="space-y-3">
        <CardDescription className="line-clamp-3">{data.description}</CardDescription>

        <div className="flex gap-2 flex-wrap">
          <Badge className={this.getStatusColor()}>{data.status}</Badge>
          <Badge className={this.getPriorityColor()}>{data.priority}</Badge>
          <Badge variant="outline">{data.issue_type}</Badge>
          {data.assigned_to_copilot && (
            <Badge className="bg-purple-100 text-purple-800">
              <Sparkles className="h-3 w-3 mr-1" />
              Copilot
            </Badge>
          )}
        </div>

        {data.github_pr_url && (
          <a href={data.github_pr_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            View PR #{data.github_pr_number}
          </a>
        )}
      </div>
    );
  }

  renderFooter() {
    const { data } = this.props;

    return (
      <>
        {data.status === "open" && !data.assigned_to_copilot && (
          <Button
            variant="default"
            size="sm"
            className="bg-purple-600 hover:bg-purple-700"
            onClick={(e) => {
              e.stopPropagation();
              this.props.onAssignToCopilot?.(data.id);
            }}
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Copilot Dev
          </Button>
        )}
      </>
    );
  }
}
```

### 4. BaseCardList (Abstract)

```typescript
// components/common/CardList/BaseCardList.tsx
import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { RefreshCw, Search } from "lucide-react";

export interface BaseCardListProps<T> {
  items: T[];
  onSync?: () => Promise<void>;
  onSearch?: (query: string) => void;
  loading?: boolean;
}

export abstract class BaseCardList<T extends { id: string }> extends React.Component<BaseCardListProps<T>, { searchQuery: string; syncing: boolean }> {
  state = {
    searchQuery: "",
    syncing: false,
  };

  abstract renderCard(item: T): React.ReactNode;
  abstract getEmptyMessage(): string;
  abstract getSyncButtonLabel(): string;

  handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    this.setState({ searchQuery: query });
    this.props.onSearch?.(query);
  };

  handleSync = async () => {
    if (!this.props.onSync) return;

    this.setState({ syncing: true });
    try {
      await this.props.onSync();
    } finally {
      this.setState({ syncing: false });
    }
  };

  filterItems(): T[] {
    const { items } = this.props;
    const { searchQuery } = this.state;

    if (!searchQuery) return items;

    return items.filter((item) => JSON.stringify(item).toLowerCase().includes(searchQuery.toLowerCase()));
  }

  render() {
    const { loading } = this.props;
    const { syncing, searchQuery } = this.state;
    const filteredItems = this.filterItems();

    return (
      <div className="space-y-4">
        {/* Header with search and sync */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input placeholder="Search..." value={searchQuery} onChange={this.handleSearch} className="pl-10" />
          </div>

          {this.props.onSync && (
            <Button onClick={this.handleSync} disabled={syncing || loading} variant="outline">
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? "animate-spin" : ""}`} />
              {this.getSyncButtonLabel()}
            </Button>
          )}
        </div>

        {/* Cards grid */}
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-8 text-gray-500">{this.getEmptyMessage()}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map((item) => (
              <div key={item.id}>{this.renderCard(item)}</div>
            ))}
          </div>
        )}
      </div>
    );
  }
}
```

### 5. RepositoryList (Concrete)

```typescript
// components/common/CardList/RepositoryList.tsx
import React from "react";
import { BaseCardList, BaseCardListProps } from "./BaseCardList";
import { RepositoryCard } from "../Card/RepositoryCard";
import { Repository } from "@/types/repository";

interface RepositoryListProps extends BaseCardListProps<Repository> {
  onSyncIssues?: (repoId: string) => void;
  onDelete?: (repoId: string) => void;
  onEdit?: (repoId: string) => void;
  onClick?: (repoId: string) => void;
}

export class RepositoryList extends BaseCardList<Repository> {
  declare props: RepositoryListProps;

  renderCard(repo: Repository) {
    return <RepositoryCard data={repo} onSync={this.props.onSyncIssues} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage() {
    return 'No repositories found. Click "Sync Repositories" to get started.';
  }

  getSyncButtonLabel() {
    return "Sync Repositories";
  }
}
```

### 6. IssueList (Concrete)

```typescript
// components/common/CardList/IssueList.tsx
import React from "react";
import { BaseCardList, BaseCardListProps } from "./BaseCardList";
import { IssueCard } from "../Card/IssueCard";
import { Issue } from "@/types/issue";

interface IssueListProps extends BaseCardListProps<Issue> {
  onAssignToCopilot?: (issueId: string) => void;
  onDelete?: (issueId: string) => void;
  onEdit?: (issueId: string) => void;
  onClick?: (issueId: string) => void;
}

export class IssueList extends BaseCardList<Issue> {
  declare props: IssueListProps;

  renderCard(issue: Issue) {
    return <IssueCard data={issue} onAssignToCopilot={this.props.onAssignToCopilot} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage() {
    return 'No issues found. Click "Sync Issues" to import from GitHub.';
  }

  getSyncButtonLabel() {
    return "Sync Issues";
  }
}
```

---

## 📝 Usage Examples

### Backend - Create an Issue

```python
from src.models.issue import IssueCreate
from src.repositories.issue_repository import IssueRepository
from src.database import Neo4jConnection

# Create issue
db = Neo4jConnection()
repo = IssueRepository(db)

issue_data = IssueCreate(
    title="Fix login bug",
    description="Users can't log in with OAuth",
    repository_id="repo-123",
    priority="urgent",
    issue_type="bug"
)

issue = await repo.create(issue_data.dict())
```

### Frontend - Display Repository List

```tsx
// pages/Repositories.tsx
import React, { useState, useEffect } from "react";
import { RepositoryList } from "@/components/common/CardList/RepositoryList";
import { useRepositories } from "@/hooks/useRepositories";
import { useNavigate } from "react-router-dom";

export function RepositoriesPage() {
  const navigate = useNavigate();
  const { repositories, loading, syncRepositories, syncIssues } = useRepositories();

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Repositories</h1>

      <RepositoryList
        items={repositories}
        loading={loading}
        onSync={syncRepositories}
        onSyncIssues={(repoId) => syncIssues(repoId)}
        onClick={(repoId) => navigate(`/development/repositories/${repoId}/issues`)}
        onDelete={(repoId) => console.log("Delete", repoId)}
        onEdit={(repoId) => console.log("Edit", repoId)}
      />
    </div>
  );
}
```

---

## 🚀 Migration Plan

### Phase 1: Backend Foundation (Week 1)

1. ✅ Create base models with proper typing
2. ✅ Implement BaseRepository with generic CRUD
3. ✅ Create concrete repositories (User, Repository, Issue, Message)
4. ✅ Write unit tests for repositories

### Phase 2: Services Layer (Week 2)

1. ✅ Refactor GitHubSyncService
2. ✅ Clean up CopilotAgentService
3. ✅ Create MessageService for PR comments
4. ✅ Write integration tests

### Phase 3: Controllers (Week 3)

1. ✅ Refactor all controllers to use new architecture
2. ✅ Add proper error handling and validation
3. ✅ Document all endpoints with OpenAPI
4. ✅ Add API tests

### Phase 4: Frontend Foundation (Week 4)

1. ✅ Create BaseCard and BaseCardList
2. ✅ Implement RepositoryCard and IssueCard
3. ✅ Create type definitions
4. ✅ Set up custom hooks

### Phase 5: Frontend Integration (Week 5)

1. ✅ Create pages with new components
2. ✅ Connect to backend APIs
3. ✅ Add loading states and error handling
4. ✅ Polish UI/UX

### Phase 6: Testing & Polish (Week 6)

1. ✅ End-to-end testing
2. ✅ Performance optimization
3. ✅ Documentation
4. ✅ Deploy

---

## ✨ Benefits of This Architecture

### Backend

- ✅ **Type Safety** - Pydantic models with validation
- ✅ **DRY** - BaseRepository eliminates repetition
- ✅ **Testability** - Each layer can be tested independently
- ✅ **Maintainability** - Clear separation of concerns
- ✅ **Scalability** - Easy to add new entities

### Frontend

- ✅ **Reusability** - Abstract components reduce code duplication
- ✅ **Consistency** - All cards/lists follow same pattern
- ✅ **Type Safety** - TypeScript throughout
- ✅ **Maintainability** - Easy to modify common behavior
- ✅ **Extensibility** - Simple to add new card types

---

## 📚 Next Steps

1. Review this architecture document
2. Approve or suggest modifications
3. Start implementation phase by phase
4. Regular code reviews after each phase

**Question**: Êtes-vous d'accord avec cette architecture ? Y a-t-il des modifications à apporter avant de commencer l'implémentation ?
