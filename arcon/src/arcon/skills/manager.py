"""Skill manager for injecting skills into agent prompts."""

from typing import Optional

from .base import Skill
from .registry import SkillRegistry


class SkillManager:
    """Manager for selecting and injecting skills into prompts."""
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        """Initialize skill manager.
        
        Args:
            registry: Skill registry to use (defaults to global registry)
        """
        self.registry = registry or SkillRegistry()
    
    def select_skills(
        self,
        query: str,
        context: Optional[dict] = None,
        explicit_skills: Optional[list[str]] = None,
        max_auto_skills: int = 3,
        min_score: float = 0.1,
    ) -> list[Skill]:
        """Select skills for a query.
        
        Combines explicitly requested skills with auto-selected relevant skills.
        
        Args:
            query: User query
            context: Optional context (e.g., file extension, language)
            explicit_skills: Explicitly requested skill names
            max_auto_skills: Maximum auto-selected skills
            min_score: Minimum relevance score for auto-selection
        
        Returns:
            List of selected skills
        """
        selected = []
        
        # Add explicitly requested skills
        if explicit_skills:
            for skill_name in explicit_skills:
                if self.registry.has(skill_name):
                    skill = self.registry.get(skill_name)
                    if skill not in selected:
                        selected.append(skill)
        
        # Add auto-selected skills if room remains
        remaining_slots = max_auto_skills - len(selected)
        if remaining_slots > 0:
            auto_skills = self.registry.find_relevant_skills(
                query=query,
                context=context,
                max_skills=remaining_slots,
                min_score=min_score,
            )
            
            for skill in auto_skills:
                if skill not in selected:
                    selected.append(skill)
        
        return selected
    
    def format_skills_for_prompt(self, skills: list[Skill]) -> list[str]:
        """Format skills for injection into prompt.
        
        Args:
            skills: List of skills to format
        
        Returns:
            List of formatted skill strings
        """
        return [skill.format_for_prompt() for skill in skills]
    
    def inject_skills(
        self,
        query: str,
        context: Optional[dict] = None,
        explicit_skills: Optional[list[str]] = None,
        max_auto_skills: int = 3,
    ) -> tuple[str, list[str]]:
        """Select and format skills for injection.
        
        This is a convenience method that combines selection and formatting.
        
        Args:
            query: User query
            context: Optional context
            explicit_skills: Explicitly requested skill names
            max_auto_skills: Maximum auto-selected skills
        
        Returns:
            Tuple of (original_query, formatted_skills)
        """
        selected = self.select_skills(
            query=query,
            context=context,
            explicit_skills=explicit_skills,
            max_auto_skills=max_auto_skills,
        )
        
        formatted = self.format_skills_for_prompt(selected)
        
        return query, formatted
    
    def compose_skills(self, skill_names: list[str]) -> str:
        """Compose multiple skills into a single content block.
        
        Useful for creating combo skills from related skills.
        
        Args:
            skill_names: List of skill names to compose
        
        Returns:
            Combined skill content
        """
        skills = []
        for name in skill_names:
            if self.registry.has(name):
                skills.append(self.registry.get(name))
        
        if not skills:
            return ""
        
        # Combine with separators
        parts = [f"# Combined Skills\n"]
        for skill in skills:
            parts.append(skill.format_for_prompt())
            parts.append("\n---\n")
        
        return "\n".join(parts)
    
    def get_skills_summary(self) -> dict:
        """Get summary of available skills.
        
        Returns:
            Dictionary with categories, tags, and counts
        """
        return {
            "total_skills": self.registry.count(),
            "categories": self.registry.get_categories(),
            "tags": self.registry.get_tags(),
            "skill_names": self.registry.list_names(),
        }
