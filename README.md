# mathsPlayz

RAG-powered educational math animation generator. Give it a topic, it plans scenes, writes Manim code, renders, and combines into a final MP4.

---

## How It Works

```
Topic → Storyboard (LLM) → Code per scene (RAG + LLM) → Render (Manim) → Combine (ffmpeg) → MP4
```

1. **Storyboard** — LLM breaks the topic into N scenes (`title` + `description`)
2. **Code Gen** — RAG retrieves relevant examples from `template/`, LLM writes a `LessonScene` class
3. **Render** — Manim renders each scene; errors are auto-fixed by the LLM (up to `MAX_RETRIES`)
4. **Combine** — ffmpeg concatenates scene clips into one final video

Scenes are processed **in parallel** via `ThreadPoolExecutor`.

---

## Project Structure

```
mathsPlayz/
├── src/
│   ├── config.py        # Reads settings from .env
│   ├── llm.py           # Ollama wrapper: ask() + extract_code()
│   ├── rag.py           # Keyword-overlap retriever over template/
│   ├── storyboard.py    # LLM → JSON list of {title, description}
│   ├── codeGen.py       # RAG + LLM → LessonScene code + fix_code()
│   ├── renderer.py      # Save → syntax check → manim render, with fix loops
│   └── pipeline.py      # Orchestrator: parallel scenes → combine → cleanup
├── template/            # RAG reference examples (Manim .py files)
├── frontend/            # Static web UI (served by FastAPI)
├── output_videos/       # Generated MP4s (created on first run)
├── app.py               # FastAPI backend + static file server
├── streamlit_app.py     # Streamlit UI (alternative to web frontend)
└── .env                 # Configuration
```

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally
- [Manim CE](https://www.manim.community/) installed in the venv
- `ffmpeg` available in PATH

---

## Setup

```bash
# Clone and enter the project
git clone <repo> && cd mathsPlayz

# Create and activate virtualenv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install manim langchain-ollama langchain-core fastapi uvicorn streamlit python-dotenv

# Pull the model
ollama pull gemma4:e2b
```

Create a `.env` file:

```env
CODEGEN_MODEL=gemma4:e2b
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11435
MAX_RETRIES=3
DEFAULT_QUALITY=l
DEFAULT_FPS=15
```

---

## Running

### Option 1 — Streamlit UI (recommended for local use)

```bash
./venv/bin/streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Type a topic, choose scene count, click **Generate**.

### Option 2 — FastAPI + Web Frontend

```bash
./venv/bin/python3 app.py
```

Opens at `http://localhost:8000`. The web UI polls `/api/status/{task_id}` for live logs.

### Option 3 — Python directly

```python
from src.pipeline import run

path = run("Pythagorean theorem", n_scenes=3, output="out.mp4")
print(path)  # absolute path to final MP4
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/generate?topic=...&n_scenes=3` | Start generation, returns `task_id` |
| `GET`  | `/api/status/{task_id}` | Returns `status`, `logs[]`, `video_url` |
| `GET`  | `/api/health` | Health check |

**Status values:** `queued` → `running` → `done` / `failed`

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEGEN_MODEL` | `gemma4:e2b` | Ollama model for code gen + fixing |
| `LLM_PROVIDER` | `ollama` | LLM backend (only Ollama supported) |
| `OLLAMA_BASE_URL` | `http://localhost:11435` | Ollama server URL |
| `MAX_RETRIES` | `3` | Max LLM fix attempts per scene |
| `DEFAULT_QUALITY` | `l` | Manim quality: `l`=480p, `m`=720p, `h`=1080p, `k`=4K |
| `DEFAULT_FPS` | `15` | Frames per second |

---

## Adding RAG Templates

Drop any valid Manim `.py` file into `template/`. The RAG system picks the most relevant examples based on keyword overlap with the scene description.

**Rules for templates:**
- Use plain list vertices for `Polygon`: `Polygon([0,0,0], [1,0,0], [0,1,0])`
- Never nest `np.array` objects inside a list as Mobject arguments
- Class name doesn't matter in templates (only in generated scenes it must be `LessonScene`)

Included templates:

| File | Demonstrates |
|------|-------------|
| `manim_sample.py` | Shape transforms, `Create`, `FadeOut` |
| `triangle_geometry.py` | `Polygon` with correct vertex syntax, `MathTex` labels |
| `number_line_bars.py` | `NumberLine`, animated dots, `Rectangle` bar charts |
| `axes_curve.py` | `Axes`, `plot()`, `get_area()`, tangent lines |

---

## Error Self-Healing

Each scene goes through two guarded loops:

1. **Syntax loop** — `py_compile` checks the file; on failure the LLM receives the error and rewrites the code
2. **Render loop** — Manim is run; on failure the full stderr is sent back to the LLM for fixing

Both loops retry up to `MAX_RETRIES` times. Failed scenes are skipped; successful ones are still combined.

---

## Ollama Setup Notes

The project expects Ollama on port `11435` (not the default `11434`). To start with the right port:

```bash
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS=/usr/share/ollama/.ollama/models ollama serve
```

Or update `OLLAMA_BASE_URL` in `.env` to match wherever your Ollama is running.
