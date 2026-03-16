"""
This module contains the SQLAlchemy ORM models and Pydantic schemas for the Notes App backend
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# SQLAlchemy models

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", backref="notes")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="tags")


class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id = Column(Integer, ForeignKey("notes.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    note = relationship("Note", backref="note_tags")
    tag = relationship("Tag", backref="note_tags")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    theme = Column(String(20), default="light")
    markdown_preview = Column(Boolean, default=True)

    user = relationship("User", backref="settings")



# Pydantic schemas

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    """Schema for user information returned to clients"""
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[EmailStr] = None


class NoteBase(BaseModel):
    title: str = Field(..., description="Title of the note")
    content: Optional[str] = Field(None, description="Markdown content of the note")


class NoteCreate(NoteBase):
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tag names")


class NoteUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]
    tags: Optional[List[str]]


class NoteOut(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TagOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    name: str = Field(..., description="Tag name")


class SettingsUpdate(BaseModel):
    theme: Optional[str]
    markdown_preview: Optional[bool]


class UserSettingsOut(BaseModel):
    theme: str
    markdown_preview: bool

    model_config = ConfigDict(from_attributes=True)
