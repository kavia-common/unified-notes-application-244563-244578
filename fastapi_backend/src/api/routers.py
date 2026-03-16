"""
All FastAPI routers for the notes app.
Grouped by:
- /api/auth
- /api/notes
- /api/tags
- /api/search
- /api/settings
"""
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .models import (
    User, UserCreate, UserOut, Token, Note, NoteOut, NoteCreate, NoteUpdate,
    Tag, TagCreate, TagOut, NoteTag, UserSettings, UserSettingsOut, SettingsUpdate
)
from .db import get_db
from .security import (
    get_password_hash, create_access_token, get_current_user, authenticate_user
)

router = APIRouter(prefix="/api", tags=["API"])


# --- AUTH ---

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
@auth_router.post("/register", response_model=UserOut, summary="Register", description="Register a new user")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@auth_router.post("/login", response_model=Token, summary="Login", description="Authenticate user and return JWT")
def login(form_data: UserCreate, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(
        data={"user_id": user.id, "sub": user.email},
        expires_delta=timedelta(hours=12)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserOut, summary="Get My Profile")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- NOTES ---

notes_router = APIRouter(prefix="/notes", tags=["Notes"])
@notes_router.post("/", response_model=NoteOut, summary="Create Note")
def create_note(note_in: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = Note(user_id=current_user.id, title=note_in.title, content=note_in.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    # Link tags if provided
    if note_in.tags:
        tags_objs = []
        for tag_name in note_in.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name, Tag.user_id == current_user.id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=current_user.id)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            tags_objs.append(tag)
            nt = NoteTag(note_id=note.id, tag_id=tag.id)
            db.add(nt)
        db.commit()
    # reload tags
    note_tags = (
        db.query(Tag.name)
        .join(NoteTag, Tag.id == NoteTag.tag_id)
        .filter(NoteTag.note_id == note.id)
        .all()
    )
    return NoteOut(
        id=note.id, user_id=note.user_id, title=note.title, content=note.content,
        created_at=note.created_at, updated_at=note.updated_at,
        tags=[t[0] for t in note_tags]
    )

@notes_router.get("/", response_model=List[NoteOut], summary="List Notes")
def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tag: Optional[str] = Query(None, description="Filter by tag name")
):
    q = db.query(Note).filter(Note.user_id == current_user.id).order_by(Note.updated_at.desc())
    if tag:
        q = q.join(NoteTag, Note.id == NoteTag.note_id).join(Tag, Tag.id == NoteTag.tag_id).filter(Tag.name == tag)
    notes = q.all()
    results = []
    for note in notes:
        tags = (
            db.query(Tag.name)
            .join(NoteTag, Tag.id == NoteTag.tag_id)
            .filter(NoteTag.note_id == note.id)
            .all()
        )
        results.append(NoteOut(
            id=note.id, user_id=note.user_id, title=note.title, content=note.content,
            created_at=note.created_at, updated_at=note.updated_at,
            tags=[t[0] for t in tags]
        ))
    return results

@notes_router.get("/{note_id}", response_model=NoteOut, summary="Get Note")
def get_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    tags = (
        db.query(Tag.name)
        .join(NoteTag, Tag.id == NoteTag.tag_id)
        .filter(NoteTag.note_id == note.id)
        .all()
    )
    return NoteOut(
        id=note.id, user_id=note.user_id, title=note.title, content=note.content,
        created_at=note.created_at, updated_at=note.updated_at,
        tags=[t[0] for t in tags]
    )

@notes_router.put("/{note_id}", response_model=NoteOut, summary="Update Note")
def update_note(note_id: int, note_upd: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_upd.title is not None:
        note.title = note_upd.title
    if note_upd.content is not None:
        note.content = note_upd.content
    db.commit()
    # Update tags
    if note_upd.tags is not None:
        # Remove all current tags
        db.query(NoteTag).filter(NoteTag.note_id == note.id).delete()
        db.commit()
        for tag_name in note_upd.tags:
            tag = db.query(Tag).filter(Tag.name == tag_name, Tag.user_id == current_user.id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=current_user.id)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            nt = NoteTag(note_id=note.id, tag_id=tag.id)
            db.add(nt)
        db.commit()
    db.refresh(note)
    tags = (
        db.query(Tag.name)
        .join(NoteTag, Tag.id == NoteTag.tag_id)
        .filter(NoteTag.note_id == note.id)
        .all()
    )
    return NoteOut(
        id=note.id, user_id=note.user_id, title=note.title, content=note.content,
        created_at=note.created_at, updated_at=note.updated_at,
        tags=[t[0] for t in tags]
    )

@notes_router.delete("/{note_id}", status_code=204, summary="Delete Note", description="Deletes a note permanently")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.query(NoteTag).filter(NoteTag.note_id == note_id).delete()
    db.delete(note)
    db.commit()
    return


# --- TAGS ---

tags_router = APIRouter(prefix="/tags", tags=["Tags"])
@tags_router.get("/", response_model=List[TagOut], summary="List Tags")
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tags = db.query(Tag).filter(Tag.user_id == current_user.id).all()
    return [TagOut(id=t.id, name=t.name) for t in tags]

@tags_router.post("/", response_model=TagOut, summary="Create Tag")
def create_tag(tag_in: TagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Tag).filter(Tag.name == tag_in.name, Tag.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tag already exists")
    tag = Tag(name=tag_in.name, user_id=current_user.id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@tags_router.delete("/{tag_id}", status_code=204, summary="Delete Tag")
def delete_tag(tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    # Remove tag links
    db.query(NoteTag).filter(NoteTag.tag_id == tag_id).delete()
    db.delete(tag)
    db.commit()
    return


# --- SEARCH ---

search_router = APIRouter(prefix="/search", tags=["Search"])
@search_router.get("/", response_model=List[NoteOut], summary="Search Notes")
def search_notes(
    q: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notes = db.query(Note).filter(
        Note.user_id == current_user.id,
        (
            Note.title.ilike(f"%{q}%") |
            Note.content.ilike(f"%{q}%")
        )
    ).order_by(Note.updated_at.desc()).all()
    results = []
    for note in notes:
        tags = (
            db.query(Tag.name)
            .join(NoteTag, Tag.id == NoteTag.tag_id)
            .filter(NoteTag.note_id == note.id)
            .all()
        )
        results.append(NoteOut(
            id=note.id, user_id=note.user_id, title=note.title, content=note.content,
            created_at=note.created_at, updated_at=note.updated_at,
            tags=[t[0] for t in tags]
        ))
    return results


# --- USER SETTINGS ---

settings_router = APIRouter(prefix="/settings", tags=["Settings"])
@settings_router.get("/", response_model=UserSettingsOut, summary="Get User Settings")
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        # create default
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@settings_router.put("/", response_model=UserSettingsOut, summary="Update User Settings")
def update_settings(upd: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    if upd.theme is not None:
        settings.theme = upd.theme
    if upd.markdown_preview is not None:
        settings.markdown_preview = upd.markdown_preview
    db.commit()
    db.refresh(settings)
    return settings
