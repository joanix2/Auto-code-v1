"""GitHub Issue Sync Service - Import GitHub issues as tickets"""
import logging
from typing import Optional, Dict, List
from github import Github, GithubException
from datetime import datetime

from ...models.ticket import Ticket, TicketCreate, TicketType, TicketPriority, TicketStatus

logger = logging.getLogger(__name__)


class GitHubIssueSyncService:
    """Service to synchronize GitHub issues with tickets"""
    
    def __init__(self, token: str):
        """
        Initialize GitHub Issue Sync Service
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.client = Github(token) if token else None
    
    def get_repository_issues(
        self, 
        repo_full_name: str,
        state: str = "open",
        labels: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get all issues from a GitHub repository
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            state: Issue state (open, closed, all)
            labels: Filter by labels
            
        Returns:
            List of issue dictionaries
        """
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return []
            
            repo = self.client.get_repo(repo_full_name)
            
            # Get issues
            issues = repo.get_issues(state=state, labels=labels or [])
            
            result = []
            for issue in issues:
                # Skip pull requests (they appear as issues in GitHub API)
                if issue.pull_request:
                    continue
                
                issue_data = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body or "",
                    "state": issue.state,
                    "html_url": issue.html_url,
                    "labels": [label.name for label in issue.labels],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                    "user": {
                        "login": issue.user.login if issue.user else None,
                        "avatar_url": issue.user.avatar_url if issue.user else None,
                    }
                }
                result.append(issue_data)
            
            logger.info(f"Retrieved {len(result)} issues from {repo_full_name}")
            return result
            
        except GithubException as e:
            logger.error(f"GitHub API error getting issues: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get issues: {e}")
            return []
    
    def map_github_issue_to_ticket_data(self, issue: Dict, repository_id: str) -> TicketCreate:
        """
        Map a GitHub issue to TicketCreate data
        
        Args:
            issue: GitHub issue dictionary
            repository_id: Repository ID in database
            
        Returns:
            TicketCreate object
        """
        # Determine ticket type from labels
        ticket_type = self._extract_type_from_labels(issue["labels"])
        
        # Determine priority from labels
        priority = self._extract_priority_from_labels(issue["labels"])
        
        # Extract description (remove metadata if it was created by AutoCode)
        description = self._clean_issue_body(issue["body"])
        
        return TicketCreate(
            title=issue["title"],
            description=description,
            repository_id=repository_id,
            priority=priority,
            ticket_type=ticket_type
        )
    
    def map_github_state_to_ticket_status(self, github_state: str) -> TicketStatus:
        """
        Map GitHub issue state to ticket status
        
        Args:
            github_state: GitHub issue state (open, closed)
            
        Returns:
            TicketStatus
        """
        if github_state == "closed":
            return TicketStatus.closed
        return TicketStatus.open
    
    def _extract_type_from_labels(self, labels: List[str]) -> TicketType:
        """
        Extract ticket type from GitHub labels
        
        Args:
            labels: List of label names
            
        Returns:
            TicketType
        """
        label_map = {
            "bug": TicketType.bugfix,
            "enhancement": TicketType.feature,
            "feature": TicketType.feature,
            "refactor": TicketType.refactor,
            "documentation": TicketType.documentation,
        }
        
        for label in labels:
            label_lower = label.lower()
            if label_lower in label_map:
                return label_map[label_lower]
        
        # Default to feature
        return TicketType.feature
    
    def _extract_priority_from_labels(self, labels: List[str]) -> TicketPriority:
        """
        Extract priority from GitHub labels
        
        Args:
            labels: List of label names
            
        Returns:
            TicketPriority
        """
        priority_map = {
            "priority: critical": TicketPriority.critical,
            "priority: high": TicketPriority.high,
            "priority: medium": TicketPriority.medium,
            "priority: low": TicketPriority.low,
            "critical": TicketPriority.critical,
            "high": TicketPriority.high,
            "medium": TicketPriority.medium,
            "low": TicketPriority.low,
        }
        
        for label in labels:
            label_lower = label.lower()
            if label_lower in priority_map:
                return priority_map[label_lower]
        
        # Default to medium
        return TicketPriority.medium
    
    def _clean_issue_body(self, body: str) -> str:
        """
        Clean issue body by removing AutoCode metadata
        
        Args:
            body: Original issue body
            
        Returns:
            Cleaned body
        """
        if not body:
            return ""
        
        # Remove AutoCode metadata section
        lines = body.split("\n")
        cleaned_lines = []
        skip_metadata = False
        
        for line in lines:
            # Start skipping when we hit the metadata separator
            if line.strip() == "---" and not skip_metadata:
                skip_metadata = True
                continue
            
            # Stop skipping after metadata section
            if skip_metadata and line.strip().startswith("_Created by AutoCode_"):
                skip_metadata = False
                continue
            
            # Add lines that are not in metadata section
            if not skip_metadata:
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines).strip()
    
    def check_if_issue_is_imported(self, issue_number: int, existing_tickets: List[Ticket]) -> Optional[Ticket]:
        """
        Check if a GitHub issue is already imported as a ticket
        
        Args:
            issue_number: GitHub issue number
            existing_tickets: List of existing tickets
            
        Returns:
            Existing ticket if found, None otherwise
        """
        for ticket in existing_tickets:
            if ticket.github_issue_number == issue_number:
                return ticket
        return None
