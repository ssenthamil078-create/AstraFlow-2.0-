"""
Phase 4 — Goal CRUD API.

Not one of the spec's numbered 6.1 API endpoints (goals/reserves are
listed as a *deliverable* of the digital twin, not a separately numbered
API in the master spec) — but a savings/reserve target has to be created
and edited somewhere for `GET /api/financial-state`'s `goals` field to
ever contain anything, so this small router exists to make that
deliverable actually usable end to end.

Phase 6 — every endpoint now scopes to the authenticated caller
(app.api.deps.get_current_user) instead of a client-supplied `user_id`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.goal import GoalORM
from app.models.user import UserORM
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.services import goal_tracking

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.post("", response_model=GoalRead)
def create_goal(
    payload: GoalCreate, current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)
):
    goal = goal_tracking.create_goal(session, current_user.id, payload)
    session.commit()
    return goal


@router.get("", response_model=list[GoalRead])
def list_goals(current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)):
    return goal_tracking.list_goals(session, current_user.id)


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    existing = goal_tracking.list_goals(session, current_user.id)
    if not any(g.id == goal_id for g in existing):
        raise HTTPException(status_code=404, detail=f"No goal with id={goal_id}")

    try:
        goal = goal_tracking.update_goal(session, goal_id, payload)
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()
    return goal


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: str,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    goal = session.query(GoalORM).filter(GoalORM.id == goal_id, GoalORM.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail=f"No goal with id={goal_id}")
    session.delete(goal)
    session.commit()
    return {"success": True, "message": "Goal removed from galaxy"}


