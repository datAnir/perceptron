"""Skill registry for managing and selecting skills."""

from typing import Optional

from .base import Skill
from ..core.interface import ConfigError


class SkillRegistry:
    """Registry for managing available skills."""
    
    def __init__(self):
        """Initialize empty skill registry."""
        self._skills: dict[str, Skill] = {}
    
    def register(self, skill: Skill) -> None:
        """Register a skill.
        
        Args:
            skill: Skill instance to register
        
        Raises:
            ConfigError: If skill name already registered
        """
        if skill.name in self._skills:
            raise ConfigError(
                f"Skill '{skill.name}' is already registered"
            )
        
        self._skills[skill.name] = skill
    
    def unregister(self, name: str) -> None:
        """Unregister a skill by name.
        
        Args:
            name: Name of skill to remove
        """
        self._skills.pop(name, None)
    
    def get(self, name: str) -> Skill:
        """Get skill by name.
        
        Args:
            name: Skill name
        
        Returns:
            Skill instance
        
        Raises:
            ConfigError: If skill not found
        """
        if name not in self._skills:
            raise ConfigError(f"Skill '{name}' not found in registry")
        
        return self._skills[name]
    
    def has(self, name: str) -> bool:
        """Check if skill is registered.
        
        Args:
            name: Skill name
        
        Returns:
            True if skill exists, False otherwise
        """
        return name in self._skills
    
    def list_all(self) -> list[Skill]:
        """List all registered skills.
        
        Returns:
            List of all skill instances
        """
        return list(self._skills.values())
    
    def list_names(self) -> list[str]:
        """List all skill names.
        
        Returns:
            Sorted list of skill names
        """
        return sorted(self._skills.keys())
    
    def get_by_category(self, category: str) -> list[Skill]:
        """Get skills by category.
        
        Args:
            category: Category to filter by
        
        Returns:
            List of skills in the category
        """
        return [
            skill for skill in self._skills.values()
            if skill.matches_category(category)
        ]
    
    def get_by_tag(self, tag: str) -> list[Skill]:
        """Get skills by tag.
        
        Args:
            tag: Tag to filter by
        
        Returns:
            List of skills with matching tag
        """
        return [
            skill for skill in self._skills.values()
            if skill.matches_tag(tag)
        ]
    
    def find_relevant_skills(
        self,
        query: str,
        context: Optional[dict] = None,
        max_skills: int = 3,
        min_score: float = 0.1,
    ) -> list[Skill]:
        """Find relevant skills for a query.
        
        Args:
            query: User query
            context: Optional context (e.g., file extension, language)
            max_skills: Maximum number of skills to return
            min_score: Minimum relevance score to include
        
        Returns:
            List of relevant skills, sorted by relevance score
        """
        # Calculate scores for all skills
        scored_skills = [
            (skill, skill.get_relevance_score(query, context))
            for skill in self._skills.values()
        ]
        
        # Filter by minimum score
        scored_skills = [
            (skill, score) for skill, score in scored_skills
            if score >= min_score
        ]
        
        # Sort by score descending
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N skills
        return [skill for skill, score in scored_skills[:max_skills]]
    
    def get_categories(self) -> list[str]:
        """Get all unique categories.
        
        Returns:
            Sorted list of categories
        """
        categories = {skill.category for skill in self._skills.values()}
        return sorted(categories)
    
    def get_tags(self) -> list[str]:
        """Get all unique tags.
        
        Returns:
            Sorted list of tags
        """
        tags = set()
        for skill in self._skills.values():
            tags.update(skill.tags)
        return sorted(tags)
    
    def clear(self) -> None:
        """Clear all registered skills."""
        self._skills.clear()
    
    def count(self) -> int:
        """Get number of registered skills.
        
        Returns:
            Number of skills
        """
        return len(self._skills)
    
    def to_dict(self) -> dict:
        """Convert registry to dictionary.
        
        Returns:
            Dictionary mapping names to skill configs
        """
        return {
            name: skill.to_dict()
            for name, skill in self._skills.items()
        }


# Global registry instance
_global_registry: Optional[SkillRegistry] = None


def get_global_registry() -> SkillRegistry:
    """Get or create global skill registry.
    
    Returns:
        Global SkillRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = SkillRegistry()
    
    return _global_registry
