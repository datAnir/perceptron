"""Tests for skills system."""

import tempfile
from pathlib import Path

import pytest

from arcon.skills import (
    Skill,
    SkillMetadata,
    SkillLoader,
    SkillManager,
    SkillRegistry,
    get_global_registry,
)
from arcon.core.interface import ConfigError


class TestSkillMetadata:
    """Test SkillMetadata class."""
    
    def test_metadata_creation(self):
        """Test creating skill metadata."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill",
            category="testing",
            tags=["test", "python"],
        )
        
        assert metadata.name == "test-skill"
        assert metadata.description == "Test skill"
        assert metadata.category == "testing"
        assert "python" in metadata.tags
    
    def test_metadata_to_dict(self):
        """Test converting metadata to dict."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill",
            category="testing",
        )
        
        data = metadata.to_dict()
        assert data["name"] == "test-skill"
        assert data["category"] == "testing"


class TestSkillBase:
    """Test Skill base class."""
    
    def test_skill_creation(self):
        """Test creating a skill."""
        metadata = SkillMetadata(
            name="python-patterns",
            description="Python design patterns",
            category="language-patterns",
            tags=["python", "design"],
        )
        content = "# Python Patterns\n\nSingleton pattern..."
        
        skill = Skill(metadata=metadata, content=content)
        
        assert skill.name == "python-patterns"
        assert skill.description == "Python design patterns"
        assert skill.category == "language-patterns"
    
    def test_skill_properties(self):
        """Test skill properties."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test",
            category="test",
            tags=["tag1", "tag2"],
        )
        skill = Skill(metadata=metadata, content="Test content")
        
        assert skill.name == "test-skill"
        assert skill.tags == ["tag1", "tag2"]
        assert skill.content == "Test content"
    
    def test_matches_tag(self):
        """Test tag matching."""
        metadata = SkillMetadata(
            name="test",
            description="Test",
            category="test",
            tags=["Python", "Django"],
        )
        skill = Skill(metadata=metadata, content="")
        
        assert skill.matches_tag("python")
        assert skill.matches_tag("PYTHON")
        assert skill.matches_tag("django")
        assert not skill.matches_tag("java")
    
    def test_matches_category(self):
        """Test category matching."""
        metadata = SkillMetadata(
            name="test",
            description="Test",
            category="Language-Patterns",
        )
        skill = Skill(metadata=metadata, content="")
        
        assert skill.matches_category("language-patterns")
        assert skill.matches_category("Language-Patterns")
        assert not skill.matches_category("testing")
    
    def test_get_relevance_score_name_match(self):
        """Test relevance scoring with name match."""
        metadata = SkillMetadata(
            name="python-patterns",
            description="Python patterns",
            category="language",
            tags=["python"],
        )
        skill = Skill(metadata=metadata, content="")
        
        score = skill.get_relevance_score("explain python-patterns")
        assert score >= 0.5  # Name match has high weight
    
    def test_get_relevance_score_tag_match(self):
        """Test relevance scoring with tag match."""
        metadata = SkillMetadata(
            name="django-patterns",
            description="Django patterns",
            category="framework",
            tags=["python", "django"],
        )
        skill = Skill(metadata=metadata, content="")
        
        score = skill.get_relevance_score("help with django")
        assert score > 0.0
    
    def test_get_relevance_score_context(self):
        """Test relevance scoring with context."""
        metadata = SkillMetadata(
            name="python-patterns",
            description="Python patterns",
            category="language",
            tags=["python"],
        )
        skill = Skill(metadata=metadata, content="")
        
        context = {"file_extension": ".py", "language": "python"}
        score = skill.get_relevance_score("review this code", context=context)
        assert score >= 0.3  # Context match
    
    def test_format_for_prompt(self):
        """Test formatting skill for prompt."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test",
            category="test",
        )
        content = "# Test Skill\n\nContent here..."
        skill = Skill(metadata=metadata, content=content)
        
        formatted = skill.format_for_prompt()
        assert "### Skill: test-skill" in formatted
        assert "Content here..." in formatted
    
    def test_skill_to_dict(self):
        """Test converting skill to dict."""
        metadata = SkillMetadata(
            name="test",
            description="Test",
            category="test",
        )
        skill = Skill(metadata=metadata, content="Test content")
        
        data = skill.to_dict()
        assert "metadata" in data
        assert "content" in data
        assert data["content"] == "Test content"


class TestSkillLoader:
    """Test SkillLoader class."""
    
    def test_load_skill_success(self):
        """Test loading skill from Markdown file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            
            skill_file = skills_dir / "test-skill.md"
            skill_file.write_text("""---
name: "test-skill"
description: "Test skill"
category: "testing"
tags: ["test", "python"]
version: "1.0.0"
---

# Test Skill

This is a test skill with markdown content.

## Usage

Use this skill for testing.
""")
            
            loader = SkillLoader(skills_dir)
            skill = loader.load_skill(skill_file)
            
            assert skill.name == "test-skill"
            assert skill.description == "Test skill"
            assert skill.category == "testing"
            assert "test" in skill.tags
            assert "This is a test skill" in skill.content
    
    def test_load_skill_file_not_found(self):
        """Test loading non-existent file."""
        loader = SkillLoader()
        
        with pytest.raises(ConfigError, match="not found"):
            loader.load_skill(Path("/nonexistent/skill.md"))
    
    def test_load_skill_no_frontmatter(self):
        """Test loading file without frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_file = skills_dir / "bad.md"
            skill_file.write_text("# Just markdown without frontmatter")
            
            loader = SkillLoader(skills_dir)
            
            with pytest.raises(ConfigError, match="frontmatter"):
                loader.load_skill(skill_file)
    
    def test_load_skill_invalid_yaml(self):
        """Test loading file with invalid YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_file = skills_dir / "bad.md"
            skill_file.write_text("""---
invalid: yaml: content:
---

Content
""")
            
            loader = SkillLoader(skills_dir)
            
            with pytest.raises(ConfigError, match="Invalid YAML"):
                loader.load_skill(skill_file)
    
    def test_load_skill_missing_fields(self):
        """Test loading file with missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir)
            skill_file = skills_dir / "incomplete.md"
            skill_file.write_text("""---
name: "incomplete"
# Missing description and category
---

Content
""")
            
            loader = SkillLoader(skills_dir)
            
            with pytest.raises(ConfigError, match="missing required fields"):
                loader.load_skill(skill_file)
    
    def test_load_all_skills(self):
        """Test loading all skills from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            
            # Create two valid skills
            for i in range(2):
                skill_file = skills_dir / f"skill{i}.md"
                skill_file.write_text(f"""---
name: "skill-{i}"
description: "Skill {i}"
category: "test"
---

Content {i}
""")
            
            loader = SkillLoader(skills_dir)
            skills = loader.load_all_skills()
            
            assert len(skills) == 2
            names = [s.name for s in skills]
            assert "skill-0" in names
            assert "skill-1" in names
    
    def test_get_skill_names(self):
        """Test getting skill names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir()
            
            (skills_dir / "skill1.md").write_text("test")
            (skills_dir / "skill2.md").write_text("test")
            
            loader = SkillLoader(skills_dir)
            names = loader.get_skill_names()
            
            assert "skill1" in names
            assert "skill2" in names


class TestSkillRegistry:
    """Test SkillRegistry class."""
    
    def test_register_skill(self):
        """Test registering a skill."""
        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="test-skill",
            description="Test",
            category="test",
        )
        skill = Skill(metadata=metadata, content="Test")
        
        registry.register(skill)
        assert registry.has("test-skill")
        assert registry.count() == 1
    
    def test_register_duplicate(self):
        """Test registering duplicate skill."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test", description="Test", category="test")
        skill1 = Skill(metadata=metadata, content="Test")
        skill2 = Skill(metadata=metadata, content="Test")
        
        registry.register(skill1)
        
        with pytest.raises(ConfigError, match="already registered"):
            registry.register(skill2)
    
    def test_get_skill(self):
        """Test getting skill by name."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test", description="Test", category="test")
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        retrieved = registry.get("test")
        assert retrieved.name == "test"
    
    def test_get_nonexistent(self):
        """Test getting non-existent skill."""
        registry = SkillRegistry()
        
        with pytest.raises(ConfigError, match="not found"):
            registry.get("nonexistent")
    
    def test_list_operations(self):
        """Test list operations."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test", description="Test", category="test")
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        assert len(registry.list_all()) == 1
        assert "test" in registry.list_names()
    
    def test_get_by_category(self):
        """Test filtering by category."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test", description="Test", category="testing")
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        testing_skills = registry.get_by_category("testing")
        assert len(testing_skills) == 1
    
    def test_get_by_tag(self):
        """Test filtering by tag."""
        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="test",
            description="Test",
            category="test",
            tags=["python"],
        )
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        python_skills = registry.get_by_tag("python")
        assert len(python_skills) == 1
    
    def test_find_relevant_skills(self):
        """Test finding relevant skills."""
        registry = SkillRegistry()
        
        # Create skills with different relevance
        for i, tag in enumerate(["python", "java", "rust"]):
            metadata = SkillMetadata(
                name=f"{tag}-skill",
                description=f"{tag} skill",
                category="language",
                tags=[tag],
            )
            skill = Skill(metadata=metadata, content=f"{tag} content")
            registry.register(skill)
        
        # Search for python
        relevant = registry.find_relevant_skills("help with python", max_skills=2)
        
        assert len(relevant) <= 2
        # Python skill should be most relevant
        if relevant:
            assert "python" in relevant[0].tags
    
    def test_get_categories(self):
        """Test getting unique categories."""
        registry = SkillRegistry()
        
        for i, cat in enumerate(["cat1", "cat2", "cat1"]):
            metadata = SkillMetadata(name=f"skill-{i}-{cat}", description="Test", category=cat)
            skill = Skill(metadata=metadata, content="Test")
            registry.register(skill)
        
        categories = registry.get_categories()
        assert len(categories) == 2
        assert "cat1" in categories
        assert "cat2" in categories
    
    def test_get_tags(self):
        """Test getting unique tags."""
        registry = SkillRegistry()
        
        metadata1 = SkillMetadata(
            name="skill1",
            description="Test",
            category="test",
            tags=["tag1", "tag2"],
        )
        metadata2 = SkillMetadata(
            name="skill2",
            description="Test",
            category="test",
            tags=["tag2", "tag3"],
        )
        
        registry.register(Skill(metadata=metadata1, content="Test"))
        registry.register(Skill(metadata=metadata2, content="Test"))
        
        tags = registry.get_tags()
        assert len(tags) == 3
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags
    
    def test_clear_registry(self):
        """Test clearing registry."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test", description="Test", category="test")
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        assert registry.count() == 1
        registry.clear()
        assert registry.count() == 0


class TestSkillManager:
    """Test SkillManager class."""
    
    def test_select_skills_explicit(self):
        """Test selecting explicitly requested skills."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test-skill", description="Test", category="test")
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        manager = SkillManager(registry=registry)
        selected = manager.select_skills(
            query="help me",
            explicit_skills=["test-skill"],
        )
        
        assert len(selected) == 1
        assert selected[0].name == "test-skill"
    
    def test_select_skills_auto(self):
        """Test auto-selecting relevant skills."""
        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="python-skill",
            description="Python skill",
            category="language",
            tags=["python"],
        )
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        manager = SkillManager(registry=registry)
        selected = manager.select_skills(
            query="help with python",
            max_auto_skills=3,
        )
        
        # Should auto-select python skill
        assert len(selected) >= 1
    
    def test_format_skills_for_prompt(self):
        """Test formatting skills for prompt."""
        registry = SkillRegistry()
        metadata = SkillMetadata(name="test", description="Test", category="test")
        skill = Skill(metadata=metadata, content="Test content")
        registry.register(skill)
        
        manager = SkillManager(registry=registry)
        formatted = manager.format_skills_for_prompt([skill])
        
        assert len(formatted) == 1
        assert "### Skill: test" in formatted[0]
    
    def test_inject_skills(self):
        """Test injecting skills."""
        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="python-skill",
            description="Python",
            category="language",
            tags=["python"],
        )
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        manager = SkillManager(registry=registry)
        query, formatted = manager.inject_skills("help with python")
        
        assert query == "help with python"
        assert isinstance(formatted, list)
    
    def test_compose_skills(self):
        """Test composing multiple skills."""
        registry = SkillRegistry()
        
        for name in ["skill1", "skill2"]:
            metadata = SkillMetadata(name=name, description="Test", category="test")
            skill = Skill(metadata=metadata, content=f"Content for {name}")
            registry.register(skill)
        
        manager = SkillManager(registry=registry)
        composed = manager.compose_skills(["skill1", "skill2"])
        
        assert "skill1" in composed
        assert "skill2" in composed
        assert "Combined Skills" in composed
    
    def test_get_skills_summary(self):
        """Test getting skills summary."""
        registry = SkillRegistry()
        metadata = SkillMetadata(
            name="test",
            description="Test",
            category="testing",
            tags=["test"],
        )
        skill = Skill(metadata=metadata, content="Test")
        registry.register(skill)
        
        manager = SkillManager(registry=registry)
        summary = manager.get_skills_summary()
        
        assert summary["total_skills"] == 1
        assert "testing" in summary["categories"]
        assert "test" in summary["tags"]
        assert "test" in summary["skill_names"]


class TestGlobalRegistry:
    """Test global skill registry."""
    
    def test_global_registry_singleton(self):
        """Test global registry is singleton."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        assert registry1 is registry2
