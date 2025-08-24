# app/routers/todos.py
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import io, csv

from ..database import get_db
from .. import models, schemas
from ..security import get_current_user

router = APIRouter(prefix="/todos", tags=["todos"])

# --------- LIST / CREATE ---------
@router.get("/", response_model=list[schemas.TodoOut])
def list_todos(
    filter: Literal["all", "done", "pending", "urgent"] = Query("all"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = db.query(models.Todo).filter(models.Todo.owner_id == user.id)
    if filter == "done":
        q = q.filter(models.Todo.completed.is_(True))
    elif filter == "pending":
        q = q.filter(models.Todo.completed.is_(False))
    elif filter == "urgent":
        q = q.filter(models.Todo.priority == 1)
    return q.order_by(models.Todo.created_at.desc()).all()

@router.post("/", response_model=schemas.TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(
    body: schemas.TodoCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    todo = models.Todo(
        title=body.title,
        notes=body.notes,
        completed=False,
        priority=body.priority,
        due_date=body.due_date,
        plan_at=body.plan_at,
        estimate_minutes=body.estimate_minutes,
        owner_id=user.id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

# --------- UPDATE / DELETE ---------
@router.put("/{todo_id}", response_model=schemas.TodoOut)
def update_todo(
    todo_id: int,
    body: schemas.TodoUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id, models.Todo.owner_id == user.id
    ).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if body.title is not None: todo.title = body.title
    if body.notes is not None: todo.notes = body.notes
    if body.completed is not None: todo.completed = body.completed
    if body.priority is not None: todo.priority = body.priority
    if body.due_date is not None: todo.due_date = body.due_date
    if body.plan_at is not None: todo.plan_at = body.plan_at
    if body.estimate_minutes is not None: todo.estimate_minutes = body.estimate_minutes

    db.commit()
    db.refresh(todo)
    return todo

# Return JSON so the frontend can res.json()
@router.delete("/{todo_id}", response_class=JSONResponse)
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id, models.Todo.owner_id == user.id
    ).first()
    if todo:
        db.delete(todo)
        db.commit()
        return {"deleted": True, "id": todo_id}
    return JSONResponse({"deleted": False, "id": todo_id}, status_code=200)

# --------- STEPS ---------
@router.post("/{todo_id}/steps", response_model=schemas.StepOut, status_code=status.HTTP_201_CREATED)
def add_step(
    todo_id: int,
    body: schemas.StepCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    todo = db.query(models.Todo).filter(
        models.Todo.id == todo_id, models.Todo.owner_id == user.id
    ).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    step = models.Step(
        todo_id=todo.id,
        text=body.text,
        done=False,
        order=(body.order if body.order is not None else 0),
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step

@router.put("/steps/{step_id}", response_model=schemas.StepOut)
def update_step(
    step_id: int,
    body: schemas.StepUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    step = (
        db.query(models.Step)
        .join(models.Todo, models.Todo.id == models.Step.todo_id)
        .filter(models.Step.id == step_id, models.Todo.owner_id == user.id)
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    if body.text is not None: step.text = body.text
    if body.done is not None: step.done = body.done
    if body.order is not None: step.order = body.order

    db.commit()
    db.refresh(step)
    return step

@router.delete("/steps/{step_id}", status_code=status.HTTP_200_OK)
def delete_step(
    step_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    step = (
        db.query(models.Step)
        .join(models.Todo, models.Todo.id == models.Step.todo_id)
        .filter(models.Step.id == step_id, models.Todo.owner_id == user.id)
        .first()
    )
    if step:
        db.delete(step)
        db.commit()
        return {"deleted": True, "id": step_id}
    return {"deleted": False, "id": step_id}

# --------- EXPORTS ---------
@router.get("/calendar.ics", include_in_schema=False)
def as_ics(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    todos = db.query(models.Todo).filter(
        models.Todo.owner_id == user.id,
        models.Todo.due_date.isnot(None),
    ).all()

    def ics_dt(dt):
        return dt.strftime("%Y%m%d")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Todo+Pomodoro//EN",
    ]
    for t in todos:
        lines += [
            "BEGIN:VEVENT",
            f"UID:todo-{t.id}@todo-pomodoro",
            f"SUMMARY:{t.title}",
            f"DESCRIPTION:{(t.notes or '').replace('\\n', ' ')}",
            f"DTSTART;VALUE=DATE:{ics_dt(t.due_date)}",
            f"DTEND;VALUE=DATE:{ics_dt(t.due_date)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return Response(content=body, media_type="text/calendar")

@router.get("/export.csv", include_in_schema=False)
def export_csv(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    todos = db.query(models.Todo).filter(models.Todo.owner_id == user.id).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","title","notes","completed","priority","due_date","plan_at","estimate_minutes","created_at","updated_at"])
    for t in todos:
        w.writerow([
            t.id, t.title, t.notes, t.completed, t.priority,
            t.due_date.isoformat() if t.due_date else "",
            t.plan_at.isoformat() if t.plan_at else "",
            t.estimate_minutes, t.created_at.isoformat(), t.updated_at.isoformat()
        ])
    buf.seek(0)
    return StreamingResponse(iter([buf.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=todos.csv"})
