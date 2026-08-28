from dataclasses import dataclass, field, asdict
from typing import Any
import json


@dataclass
class ScenePlan:
    id: str
    title: str
    description: str
    skills_required: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)  # skill_name -> param dict
    dependencies: list[str] = field(default_factory=list)  # scene IDs
    shared_assets: dict = field(default_factory=dict)
    duration_estimate: float = 10.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScenePlan":
        return cls(**data)


@dataclass
class GlobalAssets:
    color_palette: dict = field(default_factory=lambda: {
        "PRIMARY": "BLUE",
        "SECONDARY": "YELLOW",
        "ACCENT": "RED",
        "BACKGROUND": "WHITE"
    })
    font_style: str = "MathTex"
    resolution: str = "1080p"
    fps: int = 15
    quality: str = "l"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GlobalAssets":
        return cls(**data)


@dataclass
class ExecutionPlan:
    scenes: list[ScenePlan]
    global_assets: GlobalAssets
    parallel_groups: list[list[str]] = field(default_factory=list)  # scene IDs that can run in parallel

    def to_dict(self) -> dict:
        return {
            "scenes": [s.to_dict() for s in self.scenes],
            "global_assets": self.global_assets.to_dict(),
            "parallel_groups": self.parallel_groups
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionPlan":
        return cls(
            scenes=[ScenePlan.from_dict(s) for s in data["scenes"]],
            global_assets=GlobalAssets.from_dict(data["global_assets"]),
            parallel_groups=data.get("parallel_groups", [])
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlan":
        return cls.from_dict(json.loads(json_str))


def compute_parallel_groups(scenes: list[ScenePlan]) -> list[list[str]]:
    """Topological sort to find parallelizable groups."""
    # Build adjacency
    adj = {s.id: set(s.dependencies) for s in scenes}
    remaining = set(adj.keys())
    groups = []
    
    while remaining:
        # Find nodes with no unmet dependencies
        ready = [n for n in remaining if adj[n].issubset(set().union(*groups) if groups else set())]
        if not ready:
            # Circular dependency - break by taking one
            ready = [next(iter(remaining))]
        groups.append(ready)
        remaining -= set(ready)
    
    return groups


def validate_plan(plan: ExecutionPlan) -> list[str]:
    """Validate plan. Return list of errors (empty if valid)."""
    errors = []
    scene_ids = {s.id for s in plan.scenes}
    skill_names = set()  # Will be populated from registry
    
    # Check dependencies exist
    for scene in plan.scenes:
        for dep in scene.dependencies:
            if dep not in scene_ids:
                errors.append(f"Scene {scene.id}: unknown dependency '{dep}'")
    
    # Check for circular dependencies (simple check)
    visited = set()
    path = set()
    
    def visit(node_id):
        if node_id in path:
            return False
        if node_id in visited:
            return True
        path.add(node_id)
        scene = next((s for s in plan.scenes if s.id == node_id), None)
        if scene:
            for dep in scene.dependencies:
                if not visit(dep):
                    return False
        path.remove(node_id)
        visited.add(node_id)
        return True
    
    for scene in plan.scenes:
        if not visit(scene.id):
            errors.append(f"Circular dependency detected involving {scene.id}")
            break
    
    return errors