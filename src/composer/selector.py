import json
import re
from src.llm import ask, extract_code
from src.config import MODEL, BASE_URL, MAX_RETRIES
from src.skills import builtin_registry


SELECTOR_SYSTEM = """You are a Manim skill selector. Given a scene description, select the most relevant skills from the available registry.

Return ONLY a JSON array of skill selections:
[{{"skill": "skill_name", "params": {{"param1": "value1", "param2": "value2"}}}}, ...]

Rules:
- Select skills in execution order (setup → drawing → animation → labels)
- Use only skills from the provided registry
- Provide ALL required params for each skill
- Use sensible defaults for optional params
- Reference previously created mobjects by their variable names (ax, curve, poly, etc.)
- Variable naming convention: ax, nl, poly, curve, label, formula, area, tangent, dot, grid, stack, circle_group, equation
"""

def build_selector_prompt(scene: dict, rag_context: str = "") -> str:
    skills_desc = builtin_registry.get_detailed_descriptions()
    prompt = f"""Scene: {scene['title']}
Description: {scene['description']}

Available Skills:
{skills_desc}
"""
    if rag_context:
        prompt = f"Reference Examples:\n{rag_context}\n\n{prompt}"
    prompt += "\nSelect skills and parameters as JSON array:"
    return prompt


def select_skills(scene: dict, rag_context: str = "") -> list[dict]:
    """Select skills for a scene using LLM."""
    prompt = build_selector_prompt(scene, rag_context)
    
    for attempt in range(MAX_RETRIES):
        raw = ask(prompt, SELECTOR_SYSTEM, MODEL, BASE_URL)
        text = extract_code(raw).strip()
        
        try:
            # Find JSON array
            start = text.index("[")
            depth, end = 0, -1
            for i, ch in enumerate(text[start:], start):
                if ch == "[": depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            selections = json.loads(text[start:end])
            
            if isinstance(selections, list) and all("skill" in s and "params" in s for s in selections):
                # Validate skills exist
                valid = []
                for sel in selections:
                    skill = builtin_registry.get(sel["skill"])
                    if skill:
                        valid.append(sel)
                    else:
                        print(f"  ⚠ Unknown skill: {sel['skill']}, skipping")
                return valid
        except Exception as e:
            print(f"  ⚠ Skill selection attempt {attempt+1} failed: {e}")
    
    raise RuntimeError(f"Skill selection failed for: {scene['title']}")