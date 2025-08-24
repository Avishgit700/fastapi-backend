# app/schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from .utils.dates import parse_any_dt

# ---- User ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---- Steps ----
class StepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    text: str
    done: bool
    order: int

class StepCreate(BaseModel):
    text: str
    order: int = 0

class StepUpdate(BaseModel):
    text: Optional[str] = None
    done: Optional[bool] = None
    order: Optional[int] = None

# ---- Todos ----
class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class TodoCreate(BaseModel):
    title: str
    notes: str = ""
    priority: int = Field(2, ge=1, le=3)
    due_date: Optional[datetime | str] = None
    plan_at: Optional[datetime | str] = None
    estimate_minutes: int = Field(25, ge=5, le=600)
    tags: List[str] = []

    @field_validator("due_date", "plan_at", mode="before")
    @classmethod
    def _coerce_dates(cls, v):
        return parse_any_dt(v)

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    due_date: Optional[datetime | str] = None
    plan_at: Optional[datetime | str] = None
    estimate_minutes: Optional[int] = Field(None, ge=5, le=600)
    tags: Optional[List[str]] = None

    @field_validator("due_date", "plan_at", mode="before")
    @classmethod
    def _coerce_dates(cls, v):
        return parse_any_dt(v)

class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    notes: str
    completed: bool
    priority: int
    due_date: Optional[datetime]
    plan_at: Optional[datetime]
    estimate_minutes: int
    created_at: datetime
    updated_at: datetime
    tags: List[TagOut] = []
    steps: List[StepOut] = []

# ---- Pomodoro ----
class PomodoroStart(BaseModel):
    todo_id: Optional[int] = None
    duration_minutes: int = Field(25, ge=5, le=120)
    note: str = ""

class PomodoroStop(BaseModel):
    pomodoro_id: int

class PomodoroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    todo_id: Optional[int]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: int
    actual_minutes: int
    note: str
