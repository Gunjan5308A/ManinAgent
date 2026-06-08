import json
from src.llm import ask, extract_code
from src.config import MODEL, BASE_URL, MAX_RETRIES

SYSTEM = "You are a math curriculum planner. Return ONLY a valid JSON array, no markdown, no extra text."

PROMPT = """Break '{topic}' into {n} Manim animation scenes.
Return ONLY this JSON format:
[{{"title": "Scene title", "description": "Detailed description of what to animate"}}]"""

def generate_storyboard(topic: str, n: int = 3) -> list[dict]:
    for attempt in range(MAX_RETRIES):
        raw = ask(PROMPT.format(topic=topic, n=n), SYSTEM, MODEL, BASE_URL)
        text = extract_code(raw).strip()

        # find outermost JSON array
        try:
            start = text.index("[")
            # find the matching closing bracket
            depth, end = 0, -1
            for i, ch in enumerate(text[start:], start):
                if ch == "[": depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            scenes = json.loads(text[start:end])
            if isinstance(scenes, list) and all("title" in s and "description" in s for s in scenes):
                return scenes
        except Exception as e:
            print(f"  ⚠ storyboard parse attempt {attempt+1} failed: {e}")

    raise RuntimeError(f"Storyboard failed for: {topic}")
