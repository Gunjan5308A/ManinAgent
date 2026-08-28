from dataclasses import dataclass
from typing import Optional
from src.planner.schema import ScenePlan, GlobalAssets
from src.skills import builtin_registry
from src.composer.composer import generate_code, fix_composed_code
from src.renderer import render
from src.rag import RAG
import os


@dataclass
class SubAgentResult:
    scene_id: str
    video_path: Optional[str]
    error: Optional[str] = None
    code: Optional[str] = None


class SubAgent:
    def __init__(self, scene_plan: ScenePlan, global_assets: GlobalAssets, rag: RAG = None):
        self.scene_plan = scene_plan
        self.global_assets = global_assets
        self.rag = rag or RAG(os.path.join(os.path.dirname(__file__), "..", "..", "template"))

    def execute(self, scene_idx: int) -> SubAgentResult:
        """Execute a single scene plan."""
        scene_dict = {
            "title": self.scene_plan.title,
            "description": self.scene_plan.description,
        }
        
        # Get RAG context
        rag_context = self.rag.retrieve(f"{scene_dict['title']} {scene_dict['description']}")
        
        # Generate code using skill-based composer
        try:
            code = generate_code(scene_dict, self.global_assets.to_dict(), rag_context)
        except Exception as e:
            return SubAgentResult(
                scene_id=self.scene_plan.id,
                video_path=None,
                error=f"Code generation failed: {e}"
            )
        
        # Render with retries (handled by renderer)
        video_path = render(code, scene_idx)
        
        if video_path:
            return SubAgentResult(
                scene_id=self.scene_plan.id,
                video_path=video_path,
                code=code
            )
        else:
            return SubAgentResult(
                scene_id=self.scene_plan.id,
                video_path=None,
                error="Rendering failed after retries",
                code=code
            )


def run_subagent(scene_plan: ScenePlan, global_assets: GlobalAssets, scene_idx: int, rag: RAG = None) -> SubAgentResult:
    """Standalone function for pool execution."""
    agent = SubAgent(scene_plan, global_assets, rag)
    return agent.execute(scene_idx)