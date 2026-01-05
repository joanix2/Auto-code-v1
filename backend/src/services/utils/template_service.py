"""
Template Service - Jinja2 template rendering
Provides template rendering capabilities using Jinja2
"""

from jinja2 import Environment, BaseLoader, TemplateNotFound
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for rendering Jinja2 templates"""
    
    def __init__(self):
        """Initialize the template service with a basic Jinja2 environment"""
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # We control the content
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template string with the given context
        
        Args:
            template_string: Jinja2 template string
            context: Dictionary of variables to use in the template
            
        Returns:
            Rendered string
            
        Examples:
            >>> service = TemplateService()
            >>> template = "Hello {{ name }}!"
            >>> result = service.render(template, {"name": "World"})
            >>> print(result)
            Hello World!
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    def render_ticket_initial_message(
        self,
        title: str,
        description: Optional[str] = None,
        ticket_type: Optional[str] = None,
        priority: Optional[str] = None,
        repository_name: Optional[str] = None,
        **extra_context
    ) -> str:
        """
        Render the initial message for a ticket using a predefined template
        
        Args:
            title: Ticket title
            description: Ticket description
            ticket_type: Type of ticket (feature, bugfix, etc.)
            priority: Ticket priority (low, medium, high, critical)
            repository_name: Name of the repository
            **extra_context: Additional context variables
            
        Returns:
            Rendered initial message
            
        Examples:
            >>> service = TemplateService()
            >>> message = service.render_ticket_initial_message(
            ...     title="Fix login bug",
            ...     description="Users cannot login",
            ...     ticket_type="bugfix",
            ...     priority="high"
            ... )
        """
        # Default template for initial ticket message
        default_template = """# {{ title }}

{% if ticket_type %}**Type:** {{ ticket_type }}
{% endif %}{% if priority %}**Priorité:** {{ priority }}
{% endif %}{% if repository_name %}**Dépôt:** {{ repository_name }}
{% endif %}
{% if description %}
## Description

{{ description }}
{% endif %}

---

Je vais traiter ce ticket. Analysons les besoins et créons un plan d'action.
"""
        
        context = {
            "title": title,
            "description": description,
            "ticket_type": ticket_type,
            "priority": priority,
            "repository_name": repository_name,
            **extra_context
        }
        
        return self.render(default_template, context)
    
    def render_custom(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a custom template by name
        
        This is a placeholder for future file-based template loading
        
        Args:
            template_name: Name of the template
            context: Template context
            
        Returns:
            Rendered string
        """
        # For now, just return error - can be extended later
        raise NotImplementedError(
            "File-based templates not yet implemented. Use render() or render_ticket_initial_message()"
        )
