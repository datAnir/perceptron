"""Skills system for domain knowledge injection."""

from .base import Skill, SkillMetadata
from .loader import SkillLoader
from .manager import SkillManager
from .registry import SkillRegistry, get_global_registry

__all__ = [
    "Skill",
    "SkillMetadata",
    "SkillLoader",
    "SkillManager",
    "SkillRegistry",
    "get_global_registry",
]
