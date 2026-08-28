import os
import yaml
from pathlib import Path
from typing import Any
from src.skills.base import Skill, SkillParam, SkillRegistry, registry

try:
    from jinja2 import Environment, BaseLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class YamlSkill(Skill):
    def __init__(self, data: dict):
        self.name = data["name"]
        self.description = data["description"]
        self.category = data.get("category", "general")
        self.imports = data.get("imports", ["from manim import *"])
        self.template = data["template"]
        self.params = []
        for p in data.get("params", []):
            self.params.append(SkillParam(
                name=p["name"],
                type=p.get("type", "Any"),
                description=p.get("description", ""),
                default=p.get("default"),
                required=p.get("required", True)
            ))
        
        # Compile Jinja2 template if available
        if JINJA2_AVAILABLE:
            self._jinja_env = Environment(loader=BaseLoader())
            self._jinja_template = self._jinja_env.from_string(self.template)
        else:
            self._jinja_template = None

    def render(self, **kwargs) -> str:
        validated = self.validate_params(kwargs)
        
        if self._jinja_template:
            return self._jinja_template.render(**validated)
        else:
            # Fallback: simple string format (doesn't support conditionals)
            return self.template.format(**validated)


def load_skills_from_directory(directory: str | Path = None) -> SkillRegistry:
    if directory is None:
        directory = Path(__file__).parent / "templates"
    else:
        directory = Path(directory)

    reg = SkillRegistry()

    if not directory.exists():
        return reg

    for yaml_file in directory.glob("*.yaml"):
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
            if data and "name" in data:
                skill = YamlSkill(data)
                reg.register(skill)
        except Exception as e:
            print(f"Warning: Failed to load skill from {yaml_file}: {e}")

    return reg


def load_builtins() -> SkillRegistry:
    """Load all built-in skills from templates directory."""
    return load_skills_from_directory()


# Load built-in skills at module import
builtin_registry = load_builtins()

# Also register in global registry for backward compatibility
for skill in builtin_registry.all_skills():
    registry.register(skill)