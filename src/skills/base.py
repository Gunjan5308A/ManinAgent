from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import textwrap


@dataclass
class SkillParam:
    name: str
    type: str
    description: str
    default: Any = None
    required: bool = True


@dataclass
class Skill(ABC):
    name: str
    description: str
    params: list[SkillParam] = field(default_factory=list)
    imports: list[str] = field(default_factory=lambda: ["from manim import *"])
    category: str = "general"

    @abstractmethod
    def render(self, **kwargs) -> str:
        """Return code snippet for this skill with given params."""
        pass

    def validate_params(self, kwargs: dict) -> dict:
        """Validate and fill defaults. Raise ValueError if required missing."""
        result = {}
        for p in self.params:
            if p.name in kwargs:
                result[p.name] = kwargs[p.name]
            elif p.required:
                raise ValueError(f"Skill '{self.name}': missing required param '{p.name}'")
            else:
                result[p.name] = p.default
        return result

    def get_imports(self) -> str:
        return "\n".join(self.imports)

    def get_signature(self) -> str:
        parts = []
        for p in self.params:
            if p.default is not None:
                parts.append(f"{p.name}={repr(p.default)}")
            else:
                parts.append(p.name)
        return f"{self.name}({', '.join(parts)})"


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill
        self._categories.setdefault(skill.category, []).append(skill.name)

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def get_by_category(self, category: str) -> list[Skill]:
        return [self._skills[n] for n in self._categories.get(category, [])]

    def all_names(self) -> list[str]:
        return list(self._skills.keys())

    def all_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def get_descriptions(self) -> str:
        lines = []
        for skill in self._skills.values():
            params = ", ".join(f"{p.name}: {p.type}" for p in skill.params)
            lines.append(f"- {skill.name}({params}): {skill.description}")
        return "\n".join(lines)

    def get_detailed_descriptions(self) -> str:
        lines = []
        for skill in self._skills.values():
            lines.append(f"### {skill.name}")
            lines.append(f"Category: {skill.category}")
            lines.append(f"Description: {skill.description}")
            if skill.params:
                lines.append("Params:")
                for p in skill.params:
                    req = "required" if p.required else f"optional (default: {repr(p.default)})"
                    lines.append(f"  - {p.name} ({p.type}, {req}): {p.description}")
            lines.append(f"Signature: {skill.get_signature()}")
            lines.append("")
        return "\n".join(lines)


registry = SkillRegistry()