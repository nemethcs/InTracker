"""Task queue controller for monitoring and managing background tasks."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.api.middleware.auth import get_current_user, get_current_admin_user
from src.services.task_queue import task_queue

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/queue/stats")
async def get_queue_stats(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Get task queue statistics. Requires admin access."""
    stats = task_queue.get_queue_stats(task_type=task_type)
    return stats


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get task status by ID."""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Check if user has access (users can only see their own tasks)
    user_id = current_user.get("user_id")
    task_data = task.get("data", {})
    task_user_id = task_data.get("user_id")
    
    # Admin can see all tasks, users can only see their own
    if current_user.get("role") != "admin" and task_user_id and str(task_user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task",
        )
    
    # Get result if completed
    result = None
    if task.get("status") == "completed":
        result = task_queue.get_task_result(task_id)
    
    return {
        "task": task,
        "result": result,
    }
