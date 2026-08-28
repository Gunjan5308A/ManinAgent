import os
from src.llm import ask, extract_code
from src.rag import RAG
from src.config import MODEL, BASE_URL, MAX_RETRIES

rag = RAG(os.path.join(os.path.dirname(__file__), "..", "template"))

SYSTEM = """You are a Manim Community Edition (v0.18+) expert.
Write ONE complete, runnable Python scene. Requirements:
- Class MUST be named LessonScene(Scene)
- Start with: from manim import *
- Polygon vertices must be plain lists: Polygon([0,0,0], [1,0,0], [0,1,0])
- Never pass numpy arrays inside another list to Polygon/VMobject
- Use np.array only for arithmetic, not as Mobject arguments
- Return ONLY raw Python code, no markdown fences, no explanation"""

FIX_SYS = """You are a Manim CE debugger. Fix the code error shown.
- Polygon vertices must be plain lists like [x, y, 0], not np.array inside a list
- Return ONLY raw Python code, no markdown, no explanation"""

def generate_code(scene: dict) -> str:
    ctx = rag.retrieve(f"{scene['title']} {scene['description']}")
    prompt = f"Title: {scene['title']}\nAnimate: {scene['description']}"
    if ctx:
        prompt = f"Reference examples:\n{ctx}\n\n{prompt}"
    for attempt in range(MAX_RETRIES):
        code = extract_code(ask(prompt, SYSTEM, MODEL, BASE_URL))
        if "LessonScene" in code and "construct" in code:
            return code
        print(f"  ⚠ codeGen attempt {attempt+1}: invalid, retrying...")
    raise RuntimeError(f"Could not generate code for: {scene['title']}")

def fix_code(code: str, error: str) -> str:
    prompt = f"Fix this Manim code.\n\nError:\n{error[-2000:]}\n\nCode:\n{code}"
    return extract_code(ask(prompt, FIX_SYS, MODEL, BASE_URL))



