from src.skills import builtin_registry
from src.config import MAX_RETRIES
from src.llm import ask, extract_code
from src.config import MODEL, BASE_URL


COMPOSER_SYSTEM = """You are a Manim code composer. Given selected skills and global assets, produce a complete, runnable LessonScene.

Rules:
- Class MUST be named LessonScene(Scene)
- Start with: from manim import *
- Combine all skill code snippets in order
- Handle imports (deduplicate)
- Ensure variable names are consistent across skills
- Return ONLY raw Python code, no markdown, no explanation
"""

GLOBAL_IMPORTS = "from manim import *\nimport numpy as np\n"


def _indent_lines(code: str, indent: str = "        ") -> str:
    """Indent all non-empty lines."""
    lines = code.split("\n")
    return "\n".join(indent + line if line.strip() else "" for line in lines)


def compose_scene(skill_selections: list[dict], global_assets: dict) -> str:
    """Compose selected skills into a complete LessonScene."""
    
    # Collect all imports
    imports = set(["from manim import *", "import numpy as np"])
    for sel in skill_selections:
        skill = builtin_registry.get(sel["skill"])
        if skill:
            for imp in skill.imports:
                imports.add(imp)
    
    # Render each skill
    skill_code_parts = []
    for sel in skill_selections:
        skill = builtin_registry.get(sel["skill"])
        if skill:
            try:
                code = skill.render(**sel["params"])
                # Indent the skill code
                skill_code_parts.append(_indent_lines(code))
            except Exception as e:
                print(f"  ⚠ Skill {sel['skill']} render failed: {e}")
    
    # Build the scene body
    body_parts = []
    
    # Add global assets as constants at the top
    color_palette = global_assets.get("color_palette", {})
    if color_palette:
        for k, v in color_palette.items():
            body_parts.append(f"        {k} = {v}")
        body_parts.append("")  # blank line
    
    # Add skill code
    body_parts.extend(skill_code_parts)
    
    body = "\n".join(body_parts)
    
    imports_str = "\n".join(sorted(imports))
    
    scene_code = f"""{imports_str}

class LessonScene(Scene):
    def construct(self):
{body}
    self.wait(2)
"""
    return scene_code


def fix_composed_code(code: str, error: str) -> str:
    """Fix composed code using LLM."""
    from src.codeGen import FIX_SYS
    prompt = f"Fix this Manim code.\n\nError:\n{error[-2000:]}\n\nCode:\n{code}"
    return extract_code(ask(prompt, FIX_SYS, MODEL, BASE_URL))


def generate_code(scene: dict, global_assets: dict, rag_context: str = "") -> str:
    """Main entry: select skills → compose → validate."""
    from src.composer.selector import select_skills
    
    # Select skills
    selections = select_skills(scene, rag_context)
    print(f"  Selected skills: {[s['skill'] for s in selections]}")
    
    # Compose
    for attempt in range(MAX_RETRIES):
        code = compose_scene(selections, global_assets)
        if "LessonScene" in code and "construct" in code:
            return code
        print(f"  ⚠ Compose attempt {attempt+1}: invalid structure, retrying...")
    
    raise RuntimeError(f"Could not compose code for: {scene['title']}")