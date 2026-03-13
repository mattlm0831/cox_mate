from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import os
import uuid
from cox_mate.database import DatabaseManager

app = FastAPI()

BASE_DIR = Path(__file__).parent.parent
SCREENSHOT_DIR = BASE_DIR / "test_screenshots"
DB_PATH = BASE_DIR / "cox_tracker.db"

app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))

db = DatabaseManager(str(DB_PATH))

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    raids = db.get_all_raids()
    return templates.TemplateResponse("index.html", {"request": request, "raids": raids})

@app.get("/points", response_class=HTMLResponse)
def points_chart(request: Request):
    raids = db.get_all_raids()
    points = [(r.date_completed, r.points) for r in raids if r.date_completed and r.points]
    return templates.TemplateResponse("points.html", {"request": request, "points": points})

@app.get("/purples", response_class=HTMLResponse)
def purple_timeline(request: Request):
    raids = db.get_all_raids()
    purples = [r for r in raids if r.is_purple]
    return templates.TemplateResponse("purples.html", {"request": request, "purples": purples})

@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request):
    raids = db.get_all_raids()
    return templates.TemplateResponse("gallery.html", {"request": request, "raids": raids})

@app.get("/dry_streaks", response_class=HTMLResponse)
def dry_streaks(request: Request):
    raids = db.get_all_raids()
    streaks = []
    current = 0
    for r in raids:
        if r.is_purple:
            if current > 0:
                streaks.append(current)
            current = 0
        else:
            current += 1
    if current > 0:
        streaks.append(current)
    longest = max(streaks) if streaks else 0
    return templates.TemplateResponse("dry_streaks.html", {"request": request, "longest": longest, "streaks": streaks})

@app.get("/score", response_class=HTMLResponse)
def score_ui(request: Request):
    return templates.TemplateResponse("score.html", {"request": request})

@app.post("/score", response_class=HTMLResponse)
def score_run(request: Request, gemini_key: str = Form(...)):
    # This is a placeholder: you would call your scoring logic here
    # For now, just redirect to home
    # TODO: Actually trigger scoring run
    return RedirectResponse(url="/", status_code=303)
