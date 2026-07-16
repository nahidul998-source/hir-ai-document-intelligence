from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Dict, Any

from app.application.commands.review_commands import (
    ReviewCommandHandler, StartReviewCommand, SaveDraftFieldCommand,
    ApproveFieldCommand, ApproveDocumentCommand
)
from app.api.security.rbac import RequirePermission, Permissions
from app.infrastructure.database.models import User
from app.api.deps import get_current_user

from app.infrastructure.repositories.reviews import ReviewRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db

router = APIRouter(prefix="/api/v1/documents", tags=["Reviews"])

async def get_review_handler(db: AsyncSession = Depends(get_db)) -> ReviewCommandHandler:
    repo = ReviewRepository(db)
    return ReviewCommandHandler(repo)

@router.get("/{document_id}/review", dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_review_session(
    document_id: UUID, 
    current_user: User = Depends(get_current_user),
    handler: ReviewCommandHandler = Depends(get_review_handler)
):
    """
    Query: Get the active review session, field extractions, and history.
    """
    # In a production system, this queries the repository for the review session.
    # We remove the hardcoded JSON here and simulate a service call.
    session_data = await handler.get_active_session(document_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Review session not found")
    return session_data

@router.post("/{document_id}/review/start", dependencies=[Depends(RequirePermission(Permissions.REVIEW_WRITE))])
async def start_review(
    document_id: UUID, 
    current_user: User = Depends(get_current_user),
    handler: ReviewCommandHandler = Depends(get_review_handler)
):
    """Command: Start a new review session."""
    cmd = StartReviewCommand(document_id=document_id, user_id=current_user.id)
    return await handler.handle_start_review(cmd)

@router.patch("/{document_id}/review/fields/{field_name}", dependencies=[Depends(RequirePermission(Permissions.REVIEW_WRITE))])
async def save_draft_field(
    document_id: UUID, 
    field_name: str, 
    payload: Dict[str, Any], 
    current_user: User = Depends(get_current_user),
    handler: ReviewCommandHandler = Depends(get_review_handler)
):
    """Command: Save a draft modification for a specific field."""
    cmd = SaveDraftFieldCommand(
        session_id=UUID(payload.get("session_id")),
        field_name=field_name,
        edited_value=payload.get("edited_value"),
        user_id=current_user.id
    )
    return await handler.handle_save_draft(cmd)

@router.post("/{document_id}/review/fields/{field_name}/approve", dependencies=[Depends(RequirePermission(Permissions.REVIEW_APPROVE))])
async def approve_field(
    document_id: UUID, 
    field_name: str, 
    payload: Dict[str, Any], 
    current_user: User = Depends(get_current_user),
    handler: ReviewCommandHandler = Depends(get_review_handler)
):
    """Command: Mark a field as approved by human."""
    cmd = ApproveFieldCommand(
        session_id=UUID(payload.get("session_id")),
        field_name=field_name,
        user_id=current_user.id
    )
    return await handler.handle_approve_field(cmd)

@router.post("/{document_id}/review/approve", dependencies=[Depends(RequirePermission(Permissions.REVIEW_APPROVE))])
async def approve_document(
    document_id: UUID, 
    payload: Dict[str, Any], 
    current_user: User = Depends(get_current_user),
    handler: ReviewCommandHandler = Depends(get_review_handler)
):
    """Command: Approve entire document and trigger ERP push."""
    cmd = ApproveDocumentCommand(
        session_id=UUID(payload.get("session_id")),
        user_id=current_user.id
    )
    return await handler.handle_approve_document(cmd)
