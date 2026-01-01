"""Claude AI Service - Integration with Anthropic Claude API"""
import os
from typing import Optional, Dict, Any
import httpx
from datetime import datetime


class ClaudeService:
    """Service for interacting with Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude service
        
        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided and not found in environment")
        
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.max_tokens = 8000
    
    def generate_ticket_prompt(
        self,
        ticket_title: str,
        ticket_description: Optional[str],
        ticket_type: str,
        priority: str,
        repository_name: str,
        repository_path: Optional[str] = None
    ) -> str:
        """
        Generate a structured prompt for Claude to implement a ticket
        
        Args:
            ticket_title: Title of the ticket
            ticket_description: Detailed description
            ticket_type: Type (feature, bugfix, etc.)
            priority: Priority level
            repository_name: Name of the repository
            repository_path: Local path to repository (optional)
        
        Returns:
            Formatted prompt string
        """
        priority_labels = {
            "critical": "🔴 CRITIQUE",
            "high": "🟠 HAUTE",
            "medium": "🟡 MOYENNE",
            "low": "🟢 BASSE"
        }
        
        type_labels = {
            "feature": "✨ Nouvelle fonctionnalité",
            "bugfix": "🐛 Correction de bug",
            "refactor": "♻️ Refactorisation",
            "documentation": "📚 Documentation"
        }
        
        prompt = f"""# Développement Automatique - Auto-Code

## 📋 Informations du Ticket

**Titre:** {ticket_title}
**Type:** {type_labels.get(ticket_type, ticket_type)}
**Priorité:** {priority_labels.get(priority, priority)}
**Repository:** {repository_name}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 📝 Description Détaillée

{ticket_description or "Aucune description fournie"}

## 🎯 Objectif

Tu es un développeur expert. Ta mission est d'implémenter cette demande en suivant les meilleures pratiques de développement.

## ✅ Instructions

1. **Analyse du code existant**
   - Comprends l'architecture actuelle du projet
   - Identifie les patterns et conventions utilisés
   - Repère les dépendances et modules concernés

2. **Implémentation**
   - Écris du code propre, modulaire et maintenable
   - Suis les conventions du projet (style, structure, etc.)
   - Ajoute des commentaires pour les parties complexes
   - Gère les cas d'erreur de manière robuste

3. **Tests et validation**
   - Assure-toi que le code fonctionne correctement
   - Vérifie qu'il n'y a pas de régression
   - Teste les cas limites

4. **Documentation**
   - Documente les nouvelles fonctionnalités
   - Mets à jour le README si nécessaire
   - Ajoute des exemples d'utilisation si pertinent

## 📦 Livrables attendus

- Code implémenté et testé
- Fichiers modifiés/créés clairement identifiés
- Explication concise des changements effectués
- Suggestions d'améliorations futures (optionnel)

Commence l'implémentation maintenant. Fournis le code complet et les instructions de déploiement.
"""
        
        return prompt
    
    async def send_message(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Claude API and get response
        
        Args:
            prompt: User prompt/message
            system_message: Optional system message to set context
        
        Returns:
            API response containing Claude's answer
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_message:
            payload["system"] = system_message
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def develop_ticket(
        self,
        ticket_title: str,
        ticket_description: Optional[str],
        ticket_type: str,
        priority: str,
        repository_name: str,
        repository_path: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Claude to develop a ticket implementation
        
        Args:
            ticket_title: Ticket title
            ticket_description: Ticket description
            ticket_type: Type of ticket
            priority: Priority level
            repository_name: Repository name
            repository_path: Path to repository
            additional_context: Any additional context (code snippets, etc.)
        
        Returns:
            Claude's response with implementation
        """
        prompt = self.generate_ticket_prompt(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            ticket_type=ticket_type,
            priority=priority,
            repository_name=repository_name,
            repository_path=repository_path
        )
        
        if additional_context:
            prompt += f"\n\n## 📎 Contexte Additionnel\n\n{additional_context}"
        
        system_message = """Tu es un développeur senior expert avec une profonde connaissance de multiples langages de programmation et frameworks. 
Tu es capable d'analyser du code existant, de comprendre rapidement l'architecture d'un projet, et d'implémenter des fonctionnalités 
de manière propre et maintenable. Tu suis toujours les meilleures pratiques de développement et tu fournis du code de production."""
        
        response = await self.send_message(prompt, system_message)
        
        return {
            "prompt": prompt,
            "response": response,
            "content": response.get("content", [{}])[0].get("text", ""),
            "model": response.get("model"),
            "usage": response.get("usage")
        }
