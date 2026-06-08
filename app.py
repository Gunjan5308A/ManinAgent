import uuid, threading
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.pipeline import run as run_pipeline

app = FastAPI(title="mathsPlayz")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OUTPUT = Path("output_videos")
OUTPUT.mkdir(exist_ok=True)
tasks: dict = {}

def _worker(tid: str, topic: str, n: int):
    tasks[tid]["status"] = "running"
    def log(m): tasks[tid]["logs"].append(m)
    try:
        path = run_pipeline(topic, n_scenes=n, output=str(OUTPUT / f"{tid}.mp4"), log=log)
        tasks[tid]["status"] = "done" if path else "failed"
        tasks[tid]["video_url"] = f"/output_videos/{tid}.mp4" if path else None
    except Exception as e:
        tasks[tid].update({"status": "failed", "logs": tasks[tid]["logs"] + [f"ERROR: {e}"]})

@app.post("/api/generate")
def generate(topic: str = Query(...), n_scenes: int = Query(3, ge=1, le=6)):
    tid = str(uuid.uuid4())
    tasks[tid] = {"status": "queued", "logs": [], "video_url": None}
    threading.Thread(target=_worker, args=(tid, topic, n_scenes), daemon=True).start()
    return {"task_id": tid}

@app.get("/api/status/{task_id}")
def status(task_id: str):
    if task_id not in tasks: raise HTTPException(404, "Not found")
    return tasks[task_id]

@app.get("/api/health")
def health(): return {"status": "ok"}

app.mount("/output_videos", StaticFiles(directory="output_videos"), name="videos")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
