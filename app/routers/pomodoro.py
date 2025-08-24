from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Pomodoro, Todo, User
from ..schemas import PomodoroStart, PomodoroStop, PomodoroOut
from ..security import get_current_user

router = APIRouter(prefix="/pomodoro", tags=["pomodoro"])

@router.post("/start", response_model=PomodoroOut)
def start_pomodoro(
    payload: PomodoroStart,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.todo_id:
        todo = db.query(Todo).filter(Todo.id == payload.todo_id, Todo.owner_id == user.id).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
    p = Pomodoro(
        owner_id=user.id,
        todo_id=payload.todo_id,
        duration_minutes=payload.duration_minutes,
        started_at=datetime.utcnow(),
        note=payload.note,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@router.post("/stop", response_model=PomodoroOut)
def stop_pomodoro(
    payload: PomodoroStop,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = db.query(Pomodoro).filter(Pomodoro.id == payload.pomodoro_id, Pomodoro.owner_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pomodoro not found")
    if not p.ended_at:
        p.ended_at = datetime.utcnow()
        p.actual_minutes = int((p.ended_at - p.started_at).total_seconds() // 60)
        db.commit()
        db.refresh(p)
    return p

@router.get("/summary")
def pomodoro_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user), days: int = Query(7, ge=1, le=90)):
    since = datetime.utcnow() - timedelta(days=days)
    sessions = db.query(Pomodoro).filter(Pomodoro.owner_id == user.id, Pomodoro.started_at >= since).all()
    total_minutes = sum(s.actual_minutes or 0 for s in sessions)
    by_todo = {}
    for s in sessions:
        if s.todo_id:
            by_todo.setdefault(s.todo_id, 0)
            by_todo[s.todo_id] += (s.actual_minutes or 0)
    return {"sessions": len(sessions), "total_minutes": int(total_minutes), "by_todo": {str(k): int(v) for k, v in by_todo.items()}}
