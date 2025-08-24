from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


TodoTag = Table(
    "todo_tags",
    Base.metadata,
    Column("todo_id", Integer, ForeignKey("todos.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    todos = relationship("Todo", back_populates="owner", cascade="all, delete")
    pomodoros = relationship("Pomodoro", back_populates="owner", cascade="all, delete")

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    notes = Column(String, default="")
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3)

    # NEW: planning fields
    plan_at = Column(DateTime, nullable=True)           # when you plan to work on it
    estimate_minutes = Column(Integer, default=25)      # how long you think it will take

    owner = relationship("User", back_populates="todos")
    tags = relationship("Tag", secondary=TodoTag, back_populates="todos")
    pomodoros = relationship("Pomodoro", back_populates="todo", cascade="all, delete-orphan")
    # NEW: checklist steps
    steps = relationship("TodoStep", back_populates="todo", cascade="all, delete-orphan")

class TodoStep(Base):
    __tablename__ = "todo_steps"
    id = Column(Integer, primary_key=True, index=True)
    todo_id = Column(Integer, ForeignKey("todos.id"), index=True, nullable=False)
    text = Column(String, nullable=False)
    done = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    todo = relationship("Todo", back_populates="steps")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    todos = relationship("Todo", secondary=TodoTag, back_populates="tags")

class Pomodoro(Base):
    __tablename__ = "pomodoros"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    todo_id = Column(Integer, ForeignKey("todos.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=25)
    actual_minutes = Column(Integer, default=0)
    note = Column(String, default="")

    owner = relationship("User", back_populates="pomodoros")
    todo = relationship("Todo", back_populates="pomodoros")
