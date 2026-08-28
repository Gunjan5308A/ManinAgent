# mathsPlayz Refactor Plan

## Goals
1. **Manim SDK Skill-Based Code Generation** — Replace monolithic LLM generation with composable, pre-validated Manim skills
2. **Plan Agent with Scene-Splitting** — Decompose topics into executable plans with dependency graphs for parallel sub-agent execution

---

## Phase 1: Skill Infrastructure

### 1.1 Skill Registry (`src/skills/registry.py`)
- `Skill` base class with `name`, `params`, `render()` → code snippet
- `SkillRegistry` — load from YAML, validate, provide lookup
- Built-in skills for common patterns:
  - `create_axes`, `create_number_line`, `create_polygon`
  - `plot_function`, `create_area`, `create_tangent`
  - `animate_transform`, `animate_slide`, `animate_fade`
  - `layout_grid`, `layout_stack`, `layout_circle`
  - `write_formula`, `write_label`, `write_equation`

### 1.2 Skill Templates (`src/skills/templates/`)
- YAML files per skill: params, imports, code template, example usage
- Registry loads all `*.yaml` at startup

### 1.3 Migration: Templates → Skills
- Convert 4 existing templates to skill combinations
- Keep templates as fallback/legacy

---

## Phase 2: Composer (Replaces codeGen.py)

### 2.1 Skill Selector (`src/composer/selector.py`)
- LLM selects skills from registry based on scene description
- Input: scene `{title, description}`, available skills
- Output: ordered list of skill names + param values

### 2.2 Composer (`src/composer/composer.py`)
- Stitches selected skills into complete `LessonScene`
- Handles imports, class definition, `construct()` method
- Injects global assets (colors, fonts, resolution)
- Validates composed code syntax before return

### 2.3 Integration
- `generate_code(scene, global_assets)` → uses Selector + Composer
- Retains RAG for style reference
- Retains `fix_code()` for error recovery

---

## Phase 3: Plan Agent

### 3.1 Enhanced Schema (`src/planner/schema.py`)
```python
@dataclass
class ScenePlan:
    id: str
    title: str
    description: str
    skills_required: list[str]
    params: dict[str, Any]  # per-skill params
    dependencies: list[str]  # scene IDs
    shared_assets: dict
    duration_estimate: float

@dataclass
class GlobalAssets:
    color_palette: dict
    font_style: str
    resolution: str
    fps: int

@dataclass
class ExecutionPlan:
    scenes: list[ScenePlan]
    global_assets: GlobalAssets
    parallel_groups: list[list[str]]  # scene IDs that can run in parallel
```

### 3.2 Planner (`src/planner/planner.py`)
- LLM prompt produces `ExecutionPlan` JSON
- Validates: all skills exist in registry, no circular deps
- Computes `parallel_groups` via topological sort on dependencies
- Retries on parse/validation failure

---

## Phase 4: Sub-Agent Executor

### 4.1 Sub-Agent (`src/executor/subagent.py`)
- Single-responsibility: execute one `ScenePlan`
- Input: `ScenePlan`, `GlobalAssets`, skill registry
- Output: video path or error
- Uses Composer → Renderer pipeline

### 4.2 Executor Pool (`src/executor/pool.py`)
- Manages `ThreadPoolExecutor` / `ProcessPoolExecutor`
- Dispatches scenes in `parallel_groups` order
- Collects results, handles failures/retries
- Maintains execution order for dependent scenes

---

## Phase 5: Pipeline Integration

### 5.1 New Pipeline (`src/pipeline.py`)
```python
def run(topic, n_scenes=3, output="final.mp4", log=None):
    plan = Planner.generate(topic, n_scenes)
    results = ExecutorPool.execute(plan)
    return Combiner.combine(results, output)
```

### 5.2 Backward Compatibility
- Old `generate_storyboard` → deprecated, kept for fallback
- Old `generate_code` → deprecated, kept for fallback
- Config flag `USE_SKILLS=true/false` for gradual rollout

---

## File Map

### New Files
```
src/skills/
  __init__.py
  registry.py
  base.py
  templates/
    create_axes.yaml
    create_number_line.yaml
    create_polygon.yaml
    plot_function.yaml
    create_area.yaml
    create_tangent.yaml
    animate_transform.yaml
    animate_slide.yaml
    animate_fade.yaml
    layout_grid.yaml
    layout_stack.yaml
    layout_circle.yaml
    write_formula.yaml
    write_label.yaml
    write_equation.yaml

src/composer/
  __init__.py
  selector.py
  composer.py

src/planner/
  __init__.py
  schema.py
  planner.py

src/executor/
  __init__.py
  subagent.py
  pool.py
```

### Modified Files
- `src/pipeline.py` — new orchestration
- `src/codeGen.py` → deprecated, keep for fallback
- `src/storyboard.py` → deprecated, keep for fallback
- `src/config.py` — add `USE_SKILLS`, `EXECUTOR_TYPE` (thread/process)

### Untouched
- `src/renderer.py` — works with composed code
- `src/rag.py` — used by Selector for style
- `src/llm.py` — unchanged
- `app.py`, `streamlit_app.py` — unchanged API

---

## Execution Order

| Step | Task | Files |
|------|------|-------|
| 1 | Create skill registry + base classes | `src/skills/registry.py`, `src/skills/base.py` |
| 2 | Create 14 skill YAML templates | `src/skills/templates/*.yaml` |
| 3 | Implement Selector + Composer | `src/composer/selector.py`, `src/composer/composer.py` |
| 4 | Implement Planner + Schema | `src/planner/schema.py`, `src/planner/planner.py` |
| 5 | Implement SubAgent + Pool | `src/executor/subagent.py`, `src/executor/pool.py` |
| 6 | Refactor pipeline.py | `src/pipeline.py` |
| 7 | Update config.py | `src/config.py` |
| 8 | Test end-to-end | — |

---

## Acceptance Criteria

1. **Skill generation**: Given "plot x^2 with area under curve [0,2]", Selector picks `create_axes`, `plot_function`, `create_area`; Composer produces valid `LessonScene`
2. **Plan generation**: Given "Pythagorean theorem", Planner outputs 3-scene plan with skills, dependencies, parallel groups
3. **Parallel execution**: Independent scenes render concurrently; dependent scenes wait
4. **Output**: Final video identical quality to current pipeline, faster with parallel scenes
5. **Fallback**: `USE_SKILLS=false` runs old pipeline unchanged