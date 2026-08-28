import concurrent.futures
from src.planner import generate_plan, generate_storyboard_legacy
from src.composer.composer import generate_code
from src.renderer import render, combine, cleanup
from src.config import USE_SKILLS, MAX_WORKERS, EXECUTOR_TYPE
from src.executor import ExecutorPool


def run_legacy(topic: str, n_scenes: int = 3, output: str = "final.mp4", log=None) -> str | None:
    """Legacy pipeline using old storyboard + codeGen."""
    emit = lambda m: (print(m), log(m) if log else None)

    emit(f"📋 Storyboard (legacy): {topic}")
    scenes = generate_storyboard_legacy(topic, n_scenes)
    for i, s in enumerate(scenes, 1):
        emit(f"  {i}. {s['title']} — {s['description'][:70]}")

    emit(f"\n🎬 Rendering {len(scenes)} scenes (legacy)...")
    slots = [None] * len(scenes)

    def process(args):
        i, scene = args
        emit(f"  ▶ [{i}] {scene['title']}: generating...")
        code = generate_code(scene)
        emit(f"  ▶ [{i}] {scene['title']}: rendering...")
        return i, render(code, i)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
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


def run(topic: str, n_scenes: int = 3, output: str = "final.mp4", log=None) -> str | None:
    """Main pipeline entry point."""
    if not USE_SKILLS:
        return run_legacy(topic, n_scenes, output, log)
    
    emit = lambda m: (print(m), log(m) if log else None)

    emit(f"📋 Planning: {topic}")
    plan = generate_plan(topic, n_scenes)
    
    emit(f"  Scenes: {len(plan.scenes)}")
    emit(f"  Parallel groups: {len(plan.parallel_groups)}")
    for i, group in enumerate(plan.parallel_groups):
        emit(f"    Group {i+1}: {group}")
    
    emit(f"\n🎬 Executing with {EXECUTOR_TYPE} pool ({MAX_WORKERS} workers)...")
    pool = ExecutorPool(max_workers=MAX_WORKERS, executor_type=EXECUTOR_TYPE)
    results = pool.execute(plan, log=emit)
    
    # Collect successful videos in order
    videos = [r.video_path for r in results if r.video_path]
    failed = [r.scene_id for r in results if not r.video_path]
    
    if failed:
        emit(f"  ⚠ Failed scenes: {failed}")
    
    if not videos:
        emit("❌ All scenes failed.")
        return None

    emit(f"\n🔗 Combining {len(videos)}/{len(plan.scenes)} scenes...")
    out = combine(videos, output)
    cleanup()
    emit(f"✅ {out}" if out else "❌ Combine failed.")
    return out