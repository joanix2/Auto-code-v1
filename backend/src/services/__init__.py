""""""

Services - Business Logic LayerServices - Business Logic Layer

""""""

from .base_service import BaseService, SyncableService

from .user_service import UserService# Auth services

from .repository_service import RepositoryServicefrom .auth import GitHubOAuthService

from .issue_service import IssueService

from .message_service import MessageService# GitHub services

from .copilot_agent_service import CopilotAgentServicefrom .github import GitHubCopilotAgentService, GitHubSyncService



__all__ = [# Messaging services

    "BaseService",from .messaging import MessageService

    "SyncableService",

    "UserService",__all__ = [

    "RepositoryService",    # Auth

    "IssueService",    "GitHubOAuthService",

    "MessageService",    # GitHub

    "CopilotAgentService",    "GitHubCopilotAgentService",

]    "GitHubSyncService",

    # Messaging
    "MessageService",
]
