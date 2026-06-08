import os, glob, shutil, subprocess, sys
from pathlib import Path
from src.config import MAX_RETRIES, QUALITY, FPS

SCENES_DIR = Path("scenes")

def _save(code: str, idx: int) -> Path:
    SCENES_DIR.mkdir(exist_ok=True, parents=True)
    p = SCENES_DIR / f"scene_{idx}.py"
    p.write_text(code, encoding="utf-8")
    return p

def _syntax_ok(path: Path) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
    return r.returncode == 0, r.stderr

def _manim(path: Path) -> tuple[bool, str]:
    r = subprocess.run(
        ["python3", "-m", "manim", f"-q{QUALITY}", "--fps", str(FPS), str(path), "LessonScene"],
        capture_output=True, text=True
    )
    return r.returncode == 0, r.stdout + r.stderr

def render(code: str, idx: int) -> str | None:
    from src.codeGen import fix_code  # late import avoids circular

    path = _save(code, idx)
    for _ in range(MAX_RETRIES):
        ok, err = _syntax_ok(path)
        if ok:
            break
        print(f"  ⚠ scene {idx} syntax error, fixing...")
        code = fix_code(code, err)
        path = _save(code, idx)
    else:
        print(f"  ❌ scene {idx} syntax unfixable")
        return None

    for attempt in range(MAX_RETRIES):
        ok, out = _manim(path)
        if ok:
            hits = glob.glob(f"media/videos/scene_{idx}/**/*.mp4", recursive=True)
            return os.path.abspath(hits[0]) if hits else None
        print(f"  ⚠ scene {idx} render attempt {attempt+1} failed, fixing...")
        code = fix_code(code, out)   # fix the updated code each time
        path = _save(code, idx)

    print(f"  ❌ scene {idx} failed after {MAX_RETRIES} attempts")
    return None

def combine(videos: list[str], output: str = "final.mp4") -> str | None:
    if not videos:
        return None
    if len(videos) == 1:
        shutil.copy(videos[0], output)
        return os.path.abspath(output)
    with open("_concat.txt", "w") as f:
        f.writelines(f"file '{v}'\n" for v in videos)
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "_concat.txt", "-c", "copy", output], capture_output=True)
    os.remove("_concat.txt")
    return os.path.abspath(output) if r.returncode == 0 else None

def cleanup():
    if SCENES_DIR.exists():
        shutil.rmtree(SCENES_DIR)
