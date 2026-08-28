import json
from src.llm import ask, extract_code
from src.config import MODEL, BASE_URL, MAX_RETRIES
from src.skills import builtin_registry
from src.planner.schema import (
    ExecutionPlan, ScenePlan, GlobalAssets,
    compute_parallel_groups, validate_plan
)


PLANNER_SYSTEM = """You are a math animation planner. Break a topic into an executable plan for Manim scenes.

Return ONLY a valid JSON object matching this schema:
{{
  "scenes": [
    {{
      "id": "scene_1",
      "title": "Scene Title",
      "description": "Detailed description of what to animate",
      "skills_required": ["skill1", "skill2"],
      "params": {{
        "skill1": {{"param1": "value1"}},
        "skill2": {{"param2": "value2"}}
      }},
      "dependencies": [],
      "shared_assets": {{}},
      "duration_estimate": 10
    }}
  ],
  "global_assets": {{
    "color_palette": {{"PRIMARY": "BLUE", "SECONDARY": "YELLOW"}},
    "font_style": "MathTex",
    "resolution": "1080p",
    "fps": 15,
    "quality": "l"
  }}
}}

Rules:
- Use ONLY skills from the provided registry
- skills_required must match registry skill names exactly
- params: provide per-skill parameters (will be merged with skill defaults)
- dependencies: list of scene IDs that must complete first
- Plan for parallel execution: independent scenes = empty dependencies
- Duration estimate in seconds
- Return ONLY JSON, no markdown, no explanation
"""

def build_planner_prompt(topic: str, n_scenes: int) -> str:
    skills_desc = builtin_registry.get_descriptions()
    return f"""Topic: {topic}
Number of scenes: {n_scenes}

Available Skills:
{skills_desc}

Create an execution plan as JSON:"""


def generate_plan(topic: str, n_scenes: int = 3) -> ExecutionPlan:
    """Generate execution plan for a topic."""
    prompt = build_planner_prompt(topic, n_scenes)
    
    for attempt in range(MAX_RETRIES):
        raw = ask(prompt, PLANNER_SYSTEM, MODEL, BASE_URL)
        text = extract_code(raw).strip()
        
        try:
            # Find JSON object
            start = text.index("{")
            depth, end = 0, -1
            for i, ch in enumerate(text[start:], start):
                if ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            data = json.loads(text[start:end])
            
            plan = ExecutionPlan.from_dict(data)
            
            # Validate
            errors = validate_plan(plan)
            if not errors:
                # Compute parallel groups if not provided
                if not plan.parallel_groups:
                    plan.parallel_groups = compute_parallel_groups(plan.scenes)
                return plan
            else:
                print(f"  ⚠ Plan validation failed: {errors}")
                
        except Exception as e:
            print(f"  ⚠ Plan generation attempt {attempt+1} failed: {e}")
    
    raise RuntimeError(f"Plan generation failed for: {topic}")


def generate_storyboard_legacy(topic: str, n: int = 3) -> list[dict]:
    """Legacy storyboard format for backward compatibility."""
    plan = generate_plan(topic, n)
    return [
        {"title": s.title, "description": s.description}
        for s in plan.scenes
    ]