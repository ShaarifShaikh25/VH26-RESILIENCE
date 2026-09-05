import os
import sys
from pathlib import Path

# Add the project root to sys.path so 'backend' can be imported
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi.middleware.cors import CORSMiddleware
from backend.main import app

# Enable CORS for all origins (especially the frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to transparently strip '/api' prefix if request arrives as '/api/...'
@app.middleware("http")
async def strip_api_prefix(request, call_next):
    path = request.scope.get("path", "")
    if path.startswith("/api/"):
        request.scope["path"] = path[4:]  # remove '/api'
    elif path == "/api":
        request.scope["path"] = "/"
    response = await call_next(request)
    return response
