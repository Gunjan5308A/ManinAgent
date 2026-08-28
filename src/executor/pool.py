import concurrent.futures
from typing import Callable
from src.planner.schema import ExecutionPlan
from src.executor.subagent import SubAgentResult, run_subagent
from src.rag import RAG
import os


class ExecutorPool:
    def __init__(self, max_workers: int = 3, executor_type: str = "thread"):
        self.max_workers = max_workers
        self.executor_type = executor_type.lower()
        
    def _get_executor(self):
        if self.executor_type == "process":
            return concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers)
        return concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

    def execute(self, plan: ExecutionPlan, log: Callable[[str], None] = None) -> list[SubAgentResult]:
        """Execute all scenes in plan according to parallel groups."""
        results: dict[str, SubAgentResult] = {}
        rag = RAG(os.path.join(os.path.dirname(__file__), "..", "..", "template"))
        
        # Map scene_id -> ScenePlan
        scene_map = {s.id: s for s in plan.scenes}
        
        def emit(msg: str):
            if log:
                log(msg)
            print(msg)
        
        for group_idx, group in enumerate(plan.parallel_groups):
            emit(f"\n🎬 Executing group {group_idx + 1}/{len(plan.parallel_groups)}: {group}")
            
            # Prepare tasks for this group
            tasks = []
            for scene_id in group:
                scene_plan = scene_map[scene_id]
                # Find scene index (1-based)
                scene_idx = next(i for i, s in enumerate(plan.scenes, 1) if s.id == scene_id)
                tasks.append((scene_plan, plan.global_assets, scene_idx))
            
            # Execute group in parallel
            with self._get_executor() as ex:
                futures = {
                    ex.submit(run_subagent, sp, ga, si, rag): sp.id
                    for sp, ga, si in tasks
                }
                
                for future in concurrent.futures.as_completed(futures):
                    scene_id = futures[future]
                    try:
                        result = future.result()
                        results[scene_id] = result
                        status = "✔" if result.video_path else "❌"
                        emit(f"  {status} [{scene_id}] {'done' if result.video_path else 'failed'}")
                        if result.error:
                            emit(f"    Error: {result.error}")
                    except Exception as e:
                        emit(f"  ❌ [{scene_id}] exception: {e}")
                        results[scene_id] = SubAgentResult(
                            scene_id=scene_id,
                            video_path=None,
                            error=str(e)
                        )
        
        # Return results in scene order
        return [results[s.id] for s in plan.scenes]