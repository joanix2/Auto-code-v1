"""GitHub Issue Service - Synchronize tickets with GitHub issues"""
import logging
from typing import Optional, Dict, List
from github import Github, GithubException

from ...models.ticket import Ticket, TicketStatus, TicketType, TicketPriority

logger = logging.getLogger(__name__)


class GitHubIssueService:
    """Service to manage GitHub issues linked to tickets"""
    
    def __init__(self, token: str):
        """
        Initialize GitHub Issue Service
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.client = Github(token) if token else None
    
    def create_issue_from_ticket(
        self, 
        repo_full_name: str, 
        ticket: Ticket,
        branch_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a GitHub issue from a ticket
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            ticket: Ticket object
            branch_name: Optional branch name to mention
            
        Returns:
            Dict with issue_number and issue_url, or None if failed
        """
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return None
            
            repo = self.client.get_repo(repo_full_name)
            
            # Build issue body
            body = self._build_issue_body(ticket, branch_name)
            
            # Get labels based on ticket type and priority
            labels = self._get_labels_for_ticket(ticket)
            
            # Create the issue
            issue = repo.create_issue(
                title=ticket.title,
                body=body,
                labels=labels
            )
            
            result = {
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "title": issue.title,
                "state": issue.state
            }
            
            logger.info(f"Created GitHub issue #{issue.number} for ticket {ticket.id}")
            return result
            
        except GithubException as e:
            logger.error(f"GitHub API error creating issue: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None
    
    def update_issue_status(
        self, 
        repo_full_name: str, 
        issue_number: int, 
        ticket_status: TicketStatus,
        comment: Optional[str] = None
    ) -> bool:
        """
        Update GitHub issue based on ticket status
        
        Args:
            repo_full_name: Repository full name
            issue_number: GitHub issue number
            ticket_status: Current ticket status
            comment: Optional comment to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return False
            
            repo = self.client.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)
            
            # Add comment if provided
            if comment:
                issue.create_comment(comment)
                logger.info(f"Added comment to issue #{issue_number}")
            
            # Update issue state based on ticket status
            if ticket_status == TicketStatus.closed:
                if issue.state != "closed":
                    issue.edit(state="closed")
                    logger.info(f"Closed issue #{issue_number}")
            elif ticket_status == TicketStatus.cancelled:
                if issue.state != "closed":
                    issue.edit(state="closed")
                    issue.create_comment("🚫 Ticket cancelled")
                    logger.info(f"Closed issue #{issue_number} (cancelled)")
            elif ticket_status == TicketStatus.open and issue.state == "closed":
                issue.edit(state="open")
                logger.info(f"Reopened issue #{issue_number}")
            
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error updating issue: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update issue: {e}")
            return False
    
    def add_comment_to_issue(
        self, 
        repo_full_name: str, 
        issue_number: int, 
        comment: str
    ) -> bool:
        """
        Add a comment to a GitHub issue
        
        Args:
            repo_full_name: Repository full name
            issue_number: GitHub issue number
            comment: Comment text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return False
            
            repo = self.client.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)
            issue.create_comment(comment)
            
            logger.info(f"Added comment to issue #{issue_number}")
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error adding comment: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return False
    
    def get_issue_info(self, repo_full_name: str, issue_number: int) -> Optional[Dict]:
        """
        Get information about a GitHub issue
        
        Args:
            repo_full_name: Repository full name
            issue_number: GitHub issue number
            
        Returns:
            Dict with issue information, or None if failed
        """
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return None
            
            repo = self.client.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)
            
            return {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "html_url": issue.html_url,
                "body": issue.body,
                "labels": [label.name for label in issue.labels],
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error getting issue: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get issue: {e}")
            return None
    
    def link_pull_request_to_issue(
        self, 
        repo_full_name: str, 
        issue_number: int, 
        pr_number: int
    ) -> bool:
        """
        Link a pull request to an issue by adding a comment
        
        Args:
            repo_full_name: Repository full name
            issue_number: GitHub issue number
            pr_number: Pull request number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            comment = f"🔗 Pull Request #{pr_number} has been created to address this issue."
            return self.add_comment_to_issue(repo_full_name, issue_number, comment)
        except Exception as e:
            logger.error(f"Failed to link PR to issue: {e}")
            return False
    
    def notify_development_started(
        self, 
        repo_full_name: str, 
        issue_number: int, 
        branch_name: str
    ) -> bool:
        """
        Notify that development has started on an issue
        
        Args:
            repo_full_name: Repository full name
            issue_number: GitHub issue number
            branch_name: Branch name where development is happening
            
        Returns:
            True if successful, False otherwise
        """
        try:
            comment = f"🚀 Development started on branch `{branch_name}`\n\n_Automated by AutoCode_"
            return self.add_comment_to_issue(repo_full_name, issue_number, comment)
        except Exception as e:
            logger.error(f"Failed to notify development started: {e}")
            return False
    
    def notify_ci_status(
        self, 
        repo_full_name: str, 
        issue_number: int, 
        passed: bool, 
        details: Optional[str] = None
    ) -> bool:
        """
        Notify CI test results on an issue
        
        Args:
            repo_full_name: Repository full name
            issue_number: GitHub issue number
            passed: Whether tests passed
            details: Optional details about the tests
            
        Returns:
            True if successful, False otherwise
        """
        try:
            icon = "✅" if passed else "❌"
            status = "passed" if passed else "failed"
            comment = f"{icon} CI Tests {status}"
            
            if details:
                comment += f"\n\n{details}"
            
            comment += "\n\n_Automated by AutoCode_"
            
            return self.add_comment_to_issue(repo_full_name, issue_number, comment)
        except Exception as e:
            logger.error(f"Failed to notify CI status: {e}")
            return False
    
    def _build_issue_body(self, ticket: Ticket, branch_name: Optional[str] = None) -> str:
        """
        Build the issue body from ticket information
        
        Args:
            ticket: Ticket object
            branch_name: Optional branch name
            
        Returns:
            Formatted issue body
        """
        body_parts = []
        
        # Description
        if ticket.description:
            body_parts.append(ticket.description)
        
        # Metadata
        body_parts.append("\n---\n")
        body_parts.append("### 📋 Ticket Information")
        body_parts.append(f"- **Type**: {ticket.ticket_type.value.title()}")
        body_parts.append(f"- **Priority**: {ticket.priority.value.title()}")
        body_parts.append(f"- **Status**: {ticket.status.value.replace('_', ' ').title()}")
        
        if branch_name:
            body_parts.append(f"- **Branch**: `{branch_name}`")
        
        body_parts.append(f"\n_Ticket ID: `{ticket.id}`_")
        body_parts.append("_Created by AutoCode_")
        
        return "\n".join(body_parts)
    
    def _get_labels_for_ticket(self, ticket: Ticket) -> List[str]:
        """
        Get GitHub labels based on ticket type and priority
        
        Args:
            ticket: Ticket object
            
        Returns:
            List of label names
        """
        labels = []
        
        # Type labels
        type_labels = {
            TicketType.feature: "enhancement",
            TicketType.bugfix: "bug",
            TicketType.refactor: "refactor",
            TicketType.documentation: "documentation"
        }
        if ticket.ticket_type in type_labels:
            labels.append(type_labels[ticket.ticket_type])
        
        # Priority labels
        priority_labels = {
            TicketPriority.critical: "priority: critical",
            TicketPriority.high: "priority: high",
            TicketPriority.medium: "priority: medium",
            TicketPriority.low: "priority: low"
        }
        if ticket.priority in priority_labels:
            labels.append(priority_labels[ticket.priority])
        
        # Add automated label
        labels.append("autocode")
        
        return labels
