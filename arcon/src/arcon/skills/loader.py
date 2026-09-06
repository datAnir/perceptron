"""Skill loader for loading skill definitions from Markdown files."""

import re
from pathlib import Path
from typing import Optional

import yaml

from .base import Skill, SkillMetadata
from ..core.interface import ConfigError


class SkillLoader:
    """Loader for skill definitions from Markdown files."""
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """Initialize skill loader.
        
        Args:
            skills_dir: Directory containing skill Markdown files
        """
        self.skills_dir = skills_dir or Path("skills")
    
    def load_skill(self, skill_file: Path) -> Skill:
        """Load a single skill from Markdown file.
        
        Expects frontmatter format:
        ---
        name: "skill-name"
        description: "Skill description"
        category: "category"
        tags: ["tag1", "tag2"]
        version: "1.0.0"
        source: "built-in"
        author: "arcon"
        ---
        
        # Skill Content
        Markdown content here...
        
        Args:
            skill_file: Path to skill Markdown file
        
        Returns:
            Loaded Skill instance
        
        Raises:
            ConfigError: If file not found or invalid format
        """
        if not skill_file.exists():
            raise ConfigError(f"Skill file not found: {skill_file}")
        
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise ConfigError(f"Error reading skill file {skill_file}: {e}")
        
        # Parse frontmatter
        metadata_dict, skill_content = self._parse_frontmatter(content, skill_file)
        
        # Create metadata
        metadata = self._create_metadata(metadata_dict, skill_file)
        
        return Skill(metadata=metadata, content=skill_content)
    
    def _parse_frontmatter(self, content: str, skill_file: Path) -> tuple[dict, str]:
        """Parse YAML frontmatter from Markdown content.
        
        Args:
            content: Full file content
            skill_file: Path to file (for error messages)
        
        Returns:
            Tuple of (metadata_dict, content_without_frontmatter)
        
        Raises:
            ConfigError: If frontmatter is invalid
        """
        # Match frontmatter pattern: ---\n...\n---
        frontmatter_pattern = r"^---\s*\n(.*?\n)---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if not match:
            raise ConfigError(
                f"Skill file must have YAML frontmatter (--- ... ---): {skill_file}"
            )
        
        frontmatter_yaml = match.group(1)
        skill_content = match.group(2).strip()
        
        try:
            metadata_dict = yaml.safe_load(frontmatter_yaml)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML frontmatter in {skill_file}: {e}")
        
        if not isinstance(metadata_dict, dict):
            raise ConfigError(
                f"Frontmatter must be a YAML dictionary: {skill_file}"
            )
        
        return metadata_dict, skill_content
    
    def _create_metadata(self, metadata_dict: dict, skill_file: Path) -> SkillMetadata:
        """Create SkillMetadata from dictionary.
        
        Args:
            metadata_dict: Parsed metadata dictionary
            skill_file: Path to file (for error messages)
        
        Returns:
            SkillMetadata instance
        
        Raises:
            ConfigError: If required fields are missing
        """
        required_fields = ["name", "description"]
        missing = [f for f in required_fields if f not in metadata_dict]
        
        if missing:
            raise ConfigError(
                f"Skill file {skill_file} missing required fields: {', '.join(missing)}"
            )
        
        # Derive category from metadata or use default
        category = metadata_dict.get("category")
        if not category:
            # Try to derive from origin or use general
            origin = metadata_dict.get("origin", "").lower()
            if origin == "ecc":
                category = "development"
            else:
                category = "general"
        
        return SkillMetadata(
            name=metadata_dict["name"],
            description=metadata_dict["description"],
            category=category,
            tags=metadata_dict.get("tags", []),
            version=metadata_dict.get("version", "1.0.0"),
            source=metadata_dict.get("source", "built-in"),
            author=metadata_dict.get("author", "arcon"),
        )
    
    def load_all_skills(self) -> list[Skill]:
        """Load all skills from skills directory.
        
        Returns:
            List of loaded Skill instances
        """
        if not self.skills_dir.exists():
            return []
        
        skills = []
        for md_file in self.skills_dir.glob("*.md"):
            try:
                skill = self.load_skill(md_file)
                skills.append(skill)
            except ConfigError:
                # Skip invalid skill files
                continue
        
        return skills
    
    def get_skill_names(self) -> list[str]:
        """Get names of all available skills.
        
        Returns:
            List of skill names (without .md extension)
        """
        if not self.skills_dir.exists():
            return []
        
        names = []
        for md_file in self.skills_dir.glob("*.md"):
            names.append(md_file.stem)
        
        return sorted(names)
