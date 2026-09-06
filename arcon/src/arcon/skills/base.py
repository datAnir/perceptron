"""Abstract base class for skills."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    
    name: str
    description: str
    category: str  # e.g., "language-patterns", "framework", "testing"
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    source: str = "built-in"  # "built-in" or "learned"
    author: str = "arcon"
    
    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "source": self.source,
            "author": self.author,
        }


class Skill:
    """A skill represents domain knowledge that can be injected into agents.
    
    Skills contain:
    - Metadata (name, description, tags, category)
    - Content (markdown documentation, examples, patterns)
    - Relevance scoring for query matching
    """
    
    def __init__(
        self,
        metadata: SkillMetadata,
        content: str,
    ):
        """Initialize skill.
        
        Args:
            metadata: Skill metadata
            content: Skill content (markdown)
        """
        self.metadata = metadata
        self.content = content
    
    @property
    def name(self) -> str:
        """Get skill name."""
        return self.metadata.name
    
    @property
    def description(self) -> str:
        """Get skill description."""
        return self.metadata.description
    
    @property
    def category(self) -> str:
        """Get skill category."""
        return self.metadata.category
    
    @property
    def tags(self) -> list[str]:
        """Get skill tags."""
        return self.metadata.tags
    
    def matches_tag(self, tag: str) -> bool:
        """Check if skill matches a tag.
        
        Args:
            tag: Tag to match (case-insensitive)
        
        Returns:
            True if tag matches, False otherwise
        """
        tag_lower = tag.lower()
        return any(t.lower() == tag_lower for t in self.tags)
    
    def matches_category(self, category: str) -> bool:
        """Check if skill matches a category.
        
        Args:
            category: Category to match (case-insensitive)
        
        Returns:
            True if category matches, False otherwise
        """
        return self.category.lower() == category.lower()
    
    def get_relevance_score(self, query: str, context: Optional[dict] = None) -> float:
        """Calculate relevance score for a query.
        
        Simple keyword-based scoring. Can be enhanced with embeddings in Phase 2.
        
        Args:
            query: User query
            context: Optional context (e.g., file extension, language)
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        query_lower = query.lower()
        
        # Name match (high weight)
        if self.name.lower() in query_lower:
            score += 0.5
        
        # Tag matches (medium weight)
        for tag in self.tags:
            if tag.lower() in query_lower:
                score += 0.2
        
        # Category match (low weight)
        if self.category.lower() in query_lower:
            score += 0.1
        
        # Context matches (medium weight)
        if context:
            file_ext = context.get("file_extension", "").lower()
            language = context.get("language", "").lower()
            
            # Map file extensions to tags
            ext_map = {
                ".py": "python",
                ".ts": "typescript",
                ".js": "javascript",
                ".java": "java",
                ".rs": "rust",
                ".go": "go",
            }
            
            matched_tag = ext_map.get(file_ext) or language
            if matched_tag and self.matches_tag(matched_tag):
                score += 0.3
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def format_for_prompt(self) -> str:
        """Format skill content for injection into prompt.
        
        Returns:
            Formatted skill content
        """
        return f"### Skill: {self.name}\n\n{self.content}"
    
    def to_dict(self) -> dict:
        """Convert skill to dictionary.
        
        Returns:
            Dictionary with skill data
        """
        return {
            "metadata": self.metadata.to_dict(),
            "content": self.content,
        }
