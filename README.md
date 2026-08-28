# mathsPlayz

RAG-powered educational math animation generator. Give it a topic — it plans scenes, writes Manim code via **composable skills**, renders in parallel, and combines into a final MP4.

> Refactored pipeline: skill-based code generation + plan-agent with scene-splitting. Legacy path preserved behind `USE_SKILLS=false`.

---

## How It Works

### New pipeline (default, `USE_SKILLS=true`)

```
Topic → Planner (LLM → ExecutionPlan)
      → ExecutorPool (parallel groups, thread/process)
        → SubAgent per ScenePlan (Selector → Composer → Renderer)
      → Combine (ffmpeg) → MP4
```

1. **Planner** — LLM breaks topic into `N` `ScenePlan`s. Each plan declares `skills_required`, per-skill `params`, `dependencies`, `duration_estimate`, plus `GlobalAssets` (palette, font, resolution). Computes `parallel_groups` via topological sort.
2. **Selector** — For each scene, LLM selects ordered skills from the registry (with RAG context from `template/`).
3. **Composer** — Stitches skill YAML templates (Jinja2) into a complete `LessonScene` class, injects global assets, validates syntax.
4. **Renderer** — Saves `scenes/scene_{i}.py`, `py_compile` check → `manim` render. On failure the LLM fixes code (up to `MAX_RETRIES`).
5. **Combiner** — `ffmpeg concat` merges successful clips.

### Legacy pipeline (`USE_SKILLS=false`)

```
Topic → Storyboard (LLM → [{title, description}]) → CodeGen (RAG+LLM → LessonScene) → Render → Combine
```

Flat scene list, parallel `ThreadPoolExecutor`. Preserved for fallback / comparison.

---

## Project Structure

```
mathsPlayz/
├── src/
│   ├── config.py          # All settings from .env (legacy + multi-provider + skill flags)
│   ├── provider.py        # Provider abstraction: ollama/openai/google/anthropic/groq/together
│   ├── llm.py             # ask() wrapper over provider + extract_code()
│   ├── rag.py             # Keyword-overlap retriever over template/
│   ├── skills/            # ← NEW — Manim skill SDK
│   │   ├── base.py        # Skill / SkillParam / SkillRegistry
│   │   ├── registry.py    # YAML loader + Jinja2 renderer (15 built-ins)
│   │   └── templates/     # 15 skills: create_axes, plot_function, create_area, …
│   ├── composer/          # ← NEW — skill-based codegen
│   │   ├── selector.py    # LLM → [{skill, params}]
│   │   └── composer.py    # skills → LessonScene code
│   ├── planner/           # ← NEW — plan agent
│   │   ├── schema.py      # ScenePlan / GlobalAssets / ExecutionPlan + parallel groups
│   │   └── planner.py     # LLM → ExecutionPlan JSON
│   ├── executor/          # ← NEW — sub-agent pool
│   │   ├── subagent.py    # One ScenePlan → code → render
│   │   └── pool.py        # Dispatches parallel_groups via Thread/ProcessPool
│   ├── storyboard.py      # Legacy: LLM → JSON scenes (kept for fallback)
│   ├── codeGen.py         # Legacy: RAG+LLM → code + fix_code()
│   ├── renderer.py        # Save → syntax check → manim, with fix loops
│   └── pipeline.py        # Orchestrator: new path + run_legacy()
├── template/              # RAG reference examples (4 Manim .py files)
├── src/skills/templates/  # 15 skill YAMLs (loaded at import)
├── frontend/              # Static web UI (served by FastAPI)
├── output_videos/         # Generated MP4s (created on first run)
├── app.py                 # FastAPI backend + static server
├── streamlit_app.py       # Streamlit UI
├── requirements.txt       # ← NEW
├── PLAN.md                # Refactor plan + acceptance criteria
└── .env                   # Configuration (see below)
```

---

## Requirements

- Python 3.11+
- `ffmpeg` in `PATH`
- Manim CE system deps (cairo, pango, LaTeX) — see [manim.community](https://docs.manim.community/en/stable/installation/uv.html)
- At least one LLM provider:
  - **Ollama** local — `ollama serve` + `ollama pull gemma4:e2b`
  - **OpenAI / Google / Anthropic / Groq / Together** — API key + `LLM_PROVIDER`

---

## Setup

```bash
git clone https://github.com/Gunjan5308A/ManinAgent.git && cd mathsPlayz

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
# or: pip install manim python-dotenv PyYAML Jinja2 langchain-core langchain-ollama ...

# Ollama (if using local)
ollama pull gemma4:e2b
OLLAMA_HOST=127.0.0.1:11434 ollama serve
# project default is 11434 (override via OLLAMA_BASE_URL)
```

Create `.env` (all keys optional — sensible defaults):

```env
# ── Core ──
LLM_PROVIDER=ollama
CODEGEN_MODEL=gemma4:e2b
MAX_RETRIES=3
DEFAULT_QUALITY=l
DEFAULT_FPS=15
LLM_TEMPERATURE=0.0

# ── Skill system ──
USE_SKILLS=true
EXECUTOR_TYPE=thread
MAX_WORKERS=3

# ── Provider: Ollama ──
OLLAMA_MODEL=gemma4:e2b
OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_API_KEY=  # rarely needed

# ── Provider: OpenAI (or Azure-compatible) ──
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1

# ── Provider: Google AI Studio ──
GOOGLE_MODEL=gemini-1.5-flash
GOOGLE_API_KEY=...

# ── Provider: Anthropic ──
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_BASE_URL=

# ── Provider: Groq ──
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...

# ── Provider: Together AI ──
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
TOGETHER_API_KEY=...
TOGETHER_BASE_URL=https://api.together.xyz/v1
```

> Per-provider `*_BASE_URL` lets you point any OpenAI-compatible endpoint (Azure, proxies, local gateways) at the right provider.

---

## Running

### Option 1 — Streamlit UI

```bash
streamlit run streamlit_app.py
# http://localhost:8501
```

### Option 2 — FastAPI + Web Frontend

```bash
python app.py
# http://localhost:8000 → polls /api/status/{task_id}
```

### Option 3 — Python

```python
from src.pipeline import run

# New path (skills)
path = run("Pythagorean theorem", n_scenes=3, output="out.mp4")

# Force legacy path
# USE_SKILLS=false  → or: from src.pipeline import run_legacy
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/generate?topic=...&n_scenes=3` | Start generation, returns `task_id` |
| `GET`  | `/api/status/{task_id}` | `{status, logs[], video_url}` |
| `GET`  | `/api/health` | Health check |

`status`: `queued` → `running` → `done` / `failed`

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` \| `openai` \| `google` \| `anthropic` \| `groq` \| `together` |
| `CODEGEN_MODEL` | `gemma4:e2b` | Legacy fallback model |
| `OLLAMA_MODEL` / `OPENAI_MODEL` / `GOOGLE_MODEL` / `ANTHROPIC_MODEL` / `GROQ_MODEL` / `TOGETHER_MODEL` | see `.env` example | Per-provider model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama URL |
| `OPENAI_BASE_URL` / `ANTHROPIC_BASE_URL` / `TOGETHER_BASE_URL` | — | Override base URL for proxies/Azure |
| `*_API_KEY` | — | Per-provider API key (env) |
| `LLM_TEMPERATURE` | `0.0` | Sampling temperature |
| `USE_SKILLS` | `true` | `true` = new pipeline, `false` = legacy |
| `EXECUTOR_TYPE` | `thread` | `thread` or `process` pool |
| `MAX_WORKERS` | `3` | Parallel scene workers |
| `MAX_RETRIES` | `3` | LLM fix attempts per scene |
| `DEFAULT_QUALITY` | `l` | Manim: `l`=480p, `m`=720p, `h`=1080p, `k`=4K |
| `DEFAULT_FPS` | `15` | FPS |

---

## Skills

Pre-validated, composable Manim building blocks in `src/skills/templates/*.yaml`.

| Skill | Category | What it does |
|-------|----------|--------------|
| `create_axes` | coordinate | `Axes` with ranges + numbers |
| `create_number_line` | coordinate | `NumberLine` |
| `create_polygon` | shapes | `Polygon` from plain-list vertices |
| `plot_function` | graphs | `ax.plot(lambda)` + optional label |
| `create_area` | graphs | `ax.get_area()` |
| `create_tangent` | graphs | Tangent line + dot |
| `animate_transform` | animation | `Transform(a,b)` |
| `animate_slide` | animation | `m.animate.move_to()` |
| `animate_fade` | animation | `FadeIn` / `FadeOut` |
| `layout_grid` | layout | `arrange_in_grid` |
| `layout_stack` | layout | `VGroup.arrange(DOWN/RIGHT)` |
| `layout_circle` | layout | `arrange_on_circle` |
| `write_formula` | text | `MathTex` at position |
| `write_label` | text | `MathTex`/`Text` next to mobject |
| `write_equation` | text | Aligned multi-line `MathTex` |

**Adding a skill:** drop a YAML in `src/skills/templates/`:

```yaml
name: my_skill
category: shapes
description: What it does
params:
  - {name: color, type: str, default: "BLUE", required: false}
template: |
  obj = Circle(color={{ color }})
  {% if animate %}self.play(Create(obj)){% endif %}
```

Registry loads all `*.yaml` at startup — no code change needed.

---

## Adding RAG Templates

Drop any valid Manim `.py` into `template/`. Ranked by keyword overlap with scene description.

Rules:
- `Polygon` vertices as plain lists: `Polygon([0,0,0], [1,0,0], [0,1,0])`
- Never nest `np.array` inside Mobject args
- Template class name free; generated code must be `LessonScene`

Included:

| File | Demonstrates |
|------|--------------|
| `manim_sample.py` | `Create`, `Transform`, `FadeOut` |
| `triangle_geometry.py` | `Polygon` + `MathTex` labels |
| `number_line_bars.py` | `NumberLine`, animated dot, `Rectangle` bars |
| `axes_curve.py` | `Axes`, `plot()`, `get_area()`, tangent |

---

## Error Self-Healing

Each scene has two guarded loops (both `MAX_RETRIES`):

1. **Syntax** — `py_compile` → on error, LLM rewrites
2. **Render** — `manim` → on stderr, LLM fixes (full log truncated to 2k)

Failed scenes are skipped; successful ones still combine.

---

## Ollama Notes

Default `OLLAMA_BASE_URL` is `http://localhost:11434`. If your daemon runs elsewhere:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama serve
# then: OLLAMA_BASE_URL=http://localhost:11435 in .env
```

---

## See Also

- `PLAN.md` — refactor plan, file map, execution order, acceptance criteria
- `src/provider.py` — add a new LLM provider (implement `LLMProvider`)
- `src/skills/base.py` — `Skill` / `SkillRegistry` API
