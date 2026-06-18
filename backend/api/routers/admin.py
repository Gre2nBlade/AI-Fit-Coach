"""Роутер админ-панели. Вход по секрету (ADMIN_SECRET) → админ-JWT.
Все эндпоинты, кроме /login, защищены require_admin.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.api.dependencies import require_admin
from backend.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminLoginIn(BaseModel):
    secret: str


@router.post("/login")
async def login(payload: AdminLoginIn) -> dict:
    result = admin_service.login(payload.secret)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный секрет")
    return result


@router.get("/stats", dependencies=[Depends(require_admin)])
async def stats() -> dict:
    return await admin_service.stats()


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    return await admin_service.users(q, limit, offset)


@router.get("/users/{user_id}", dependencies=[Depends(require_admin)])
async def user_detail(user_id: int) -> dict:
    data = await admin_service.user_detail(user_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return data


@router.post("/users/{user_id}", dependencies=[Depends(require_admin)])
async def update_user(user_id: int, payload: dict) -> dict:
    if not await admin_service.user_exists(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    try:
        updated = await admin_service.update_user(user_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return updated


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: int) -> dict:
    ok = await admin_service.delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return {"deleted": True}


@router.delete("/users/{user_id}/plans/{kind}", dependencies=[Depends(require_admin)])
async def delete_plan(user_id: int, kind: str) -> dict:
    ok = await admin_service.delete_plan(user_id, kind)
    return {"deleted": ok}


@router.post("/users/{user_id}/plans/{kind}/regenerate", dependencies=[Depends(require_admin)])
async def regenerate_plan(user_id: int, kind: str) -> dict:
    if kind not in ("workout", "nutrition"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="bad kind")
    plan = await admin_service.regenerate_plan(user_id, kind)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return {"kind": kind, "plan": plan}


@router.get("/logs", dependencies=[Depends(require_admin)])
async def logs(lines: int = Query(default=200, ge=1, le=2000)) -> dict:
    return {"text": admin_service.read_logs(lines)}
