from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    auth_router,
    notes_router,
    tags_router,
    search_router,
    settings_router,
)

app = FastAPI(
    title="Unified Notes API",
    version="1.0.0",
    description="FastAPI backend for the Unified Notes App. Features: JWT auth, CRUD for notes and tags, search, and user settings.",
    openapi_tags=[
        {"name": "Authentication", "description": "User registration and JWT login"},
        {"name": "Notes", "description": "Create, edit, delete, and list notes"},
        {"name": "Tags", "description": "Manage user tags"},
        {"name": "Settings", "description": "User settings (theme, markdown preview, etc)"},
        {"name": "Search", "description": "Search notes"},
        {"name": "API", "description": "Other base endpoints"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for deployment or use env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(tags_router)
app.include_router(search_router)
app.include_router(settings_router)

@app.get("/", tags=["API"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}
