import concurrent.futures
from src.storyboard import generate_storyboard
from src.codeGen import generate_code
from src.renderer import render, combine, cleanup

def run(topic: str, n_scenes: int = 3, output: str = "final.mp4", log=None) -> str | None:
    emit = lambda m: (print(m), log(m) if log else None)

    emit(f"📋 Storyboard: {topic}")
    scenes = generate_storyboard(topic, n_scenes)
    for i, s in enumerate(scenes, 1):
        emit(f"  {i}. {s['title']} — {s['description'][:70]}")

    emit(f"\n🎬 Rendering {len(scenes)} scenes...")
    slots = [None] * len(scenes)

    def process(args):
        i, scene = args
        emit(f"  ▶ [{i}] {scene['title']}: generating...")
        code = generate_code(scene)
        emit(f"  ▶ [{i}] {scene['title']}: rendering...")
        return i, render(code, i)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        for i, path in ex.map(process, enumerate(scenes, 1)):
            slots[i - 1] = path
            emit(f"  {'✔' if path else '❌'} [{i}] {'done' if path else 'failed'}")

    videos = [v for v in slots if v]
    if not videos:
        emit("❌ All scenes failed.")
        return None

    emit(f"\n🔗 Combining {len(videos)}/{len(scenes)} scenes...")
    out = combine(videos, output)
    cleanup()
    emit(f"✅ {out}" if out else "❌ Combine failed.")
    return out
