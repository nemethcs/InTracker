"""Audit trail controller."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from src.database.base import get_db
from src.database.models import (
    Project, Feature, Todo, ProjectElement, Document, Session as SessionModel, Idea,
    User
)
from src.api.middleware.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get audit trail for a specific entity.
    
    Returns created_by, updated_by, created_at, updated_at information.
    
    Supported entity types: project, feature, todo, element, document, session, idea
    """
    # Map entity type to model
    entity_models = {
        "project": Project,
        "feature": Feature,
        "todo": Todo,
        "element": ProjectElement,
        "document": Document,
        "session": SessionModel,
        "idea": Idea,
    }
    
    if entity_type not in entity_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity type. Supported types: {', '.join(entity_models.keys())}",
        )
    
    model = entity_models[entity_type]
    entity = db.query(model).filter(model.id == entity_id).first()
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type.capitalize()} not found",
        )
    
    # Get creator and updater user info
    creator = None
    updater = None
    
    if hasattr(entity, 'created_by') and entity.created_by:
        creator_user = db.query(User).filter(User.id == entity.created_by).first()
        if creator_user:
            creator = {
                "id": str(creator_user.id),
                "email": creator_user.email,
                "full_name": creator_user.full_name,
            }
    
    if hasattr(entity, 'updated_by') and entity.updated_by:
        updater_user = db.query(User).filter(User.id == entity.updated_by).first()
        if updater_user:
            updater = {
                "id": str(updater_user.id),
                "email": updater_user.email,
                "full_name": updater_user.full_name,
            }
    
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "created_by": creator,
        "updated_by": updater,
        "created_at": entity.created_at,
        "updated_at": entity.updated_at,
    }


@router.get("/user/{user_id}/created")
async def get_user_created_entities(
    user_id: UUID,
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all entities created by a specific user.
    
    Optionally filter by entity type.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    results = []
    
    # Define entity types to query
    entity_types = {
        "project": Project,
        "feature": Feature,
        "todo": Todo,
        "element": ProjectElement,
        "document": Document,
        "session": SessionModel,
        "idea": Idea,
    }
    
    # Filter by entity type if specified
    if entity_type:
        if entity_type not in entity_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type. Supported types: {', '.join(entity_types.keys())}",
            )
        entity_types = {entity_type: entity_types[entity_type]}
    
    # Query each entity type
    for etype, model in entity_types.items():
        if hasattr(model, 'created_by'):
            entities = (
                db.query(model)
                .filter(model.created_by == user_id)
                .order_by(model.created_at.desc())
                .limit(limit)
                .all()
            )
            
            for entity in entities:
                result = {
                    "entity_type": etype,
                    "entity_id": str(entity.id),
                    "created_at": entity.created_at,
                }
                
                # Add entity-specific info
                if hasattr(entity, 'name'):
                    result["name"] = entity.name
                elif hasattr(entity, 'title'):
                    result["title"] = entity.title
                
                results.append(result)
    
    # Sort by created_at descending
    results.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "user_id": str(user_id),
        "user_email": user.email,
        "user_full_name": user.full_name,
        "total": len(results),
        "entities": results[:limit],
    }


@router.get("/user/{user_id}/updated")
async def get_user_updated_entities(
    user_id: UUID,
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all entities updated by a specific user.
    
    Optionally filter by entity type.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    results = []
    
    # Define entity types to query
    entity_types = {
        "project": Project,
        "feature": Feature,
        "todo": Todo,
        "element": ProjectElement,
        "document": Document,
        "session": SessionModel,
        "idea": Idea,
    }
    
    # Filter by entity type if specified
    if entity_type:
        if entity_type not in entity_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type. Supported types: {', '.join(entity_types.keys())}",
            )
        entity_types = {entity_type: entity_types[entity_type]}
    
    # Query each entity type
    for etype, model in entity_types.items():
        if hasattr(model, 'updated_by'):
            entities = (
                db.query(model)
                .filter(model.updated_by == user_id)
                .order_by(model.updated_at.desc())
                .limit(limit)
                .all()
            )
            
            for entity in entities:
                result = {
                    "entity_type": etype,
                    "entity_id": str(entity.id),
                    "updated_at": entity.updated_at,
                }
                
                # Add entity-specific info
                if hasattr(entity, 'name'):
                    result["name"] = entity.name
                elif hasattr(entity, 'title'):
                    result["title"] = entity.title
                
                results.append(result)
    
    # Sort by updated_at descending
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return {
        "user_id": str(user_id),
        "user_email": user.email,
        "user_full_name": user.full_name,
        "total": len(results),
        "entities": results[:limit],
    }
