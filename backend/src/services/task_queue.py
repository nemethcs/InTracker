"""Background task queue service for heavy operations.

This service provides a simple task queue implementation using Redis.
Tasks are queued and processed asynchronously by background workers.

Features:
- Task queuing with Redis
- Task status tracking
- Retry logic for failed tasks
- Priority support
- Task result storage
"""
import json
import logging
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from src.services.cache_service import get_redis_client

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskQueue:
    """Simple task queue implementation using Redis.
    
    This is a lightweight task queue suitable for:
    - Email sending
    - GitHub API operations
    - Data import/export
    - File processing
    
    For more advanced features (scheduled tasks, task dependencies, etc.),
    consider migrating to Celery in the future.
    """
    
    QUEUE_PREFIX = "task_queue:"
    TASK_PREFIX = "task:"
    RESULT_PREFIX = "task_result:"
    DEFAULT_TTL = 86400  # 24 hours
    
    def __init__(self):
        """Initialize task queue."""
        self.redis = get_redis_client()
    
    def enqueue(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        priority: int = 0,
        max_retries: int = 3,
        delay_seconds: int = 0,
    ) -> str:
        """Enqueue a task for background processing.
        
        Args:
            task_type: Type of task (e.g., "send_email", "github_import")
            task_data: Task data dictionary
            priority: Task priority (higher = more priority, default: 0)
            max_retries: Maximum number of retry attempts (default: 3)
            delay_seconds: Delay before processing (default: 0)
            
        Returns:
            Task ID (UUID string)
        """
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "type": task_type,
            "data": task_data,
            "status": TaskStatus.PENDING.value,
            "priority": priority,
            "max_retries": max_retries,
            "retry_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "delay_until": (datetime.utcnow() + timedelta(seconds=delay_seconds)).isoformat() if delay_seconds > 0 else None,
        }
        
        # Store task metadata
        task_key = f"{self.TASK_PREFIX}{task_id}"
        self.redis.setex(
            task_key,
            self.DEFAULT_TTL,
            json.dumps(task)
        )
        
        # Add to queue (sorted by priority, then creation time)
        queue_key = f"{self.QUEUE_PREFIX}{task_type}"
        # Use sorted set with score = (priority * 1000000) + timestamp
        # Higher priority = higher score = processed first
        score = (priority * 1000000) + (datetime.utcnow().timestamp() * 1000)
        self.redis.zadd(queue_key, {task_id: score})
        
        logger.info(f"Task {task_id} of type {task_type} enqueued with priority {priority}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dictionary or None if not found
        """
        task_key = f"{self.TASK_PREFIX}{task_id}"
        task_data = self.redis.get(task_key)
        if task_data:
            return json.loads(task_data)
        return None
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update task status.
        
        Args:
            task_id: Task ID
            status: New status
            result: Task result (if completed)
            error: Error message (if failed)
            
        Returns:
            True if updated, False if task not found
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        task["status"] = status.value
        task["updated_at"] = datetime.utcnow().isoformat()
        
        if status == TaskStatus.COMPLETED and result:
            task["result"] = result
            # Store result separately for longer retention
            result_key = f"{self.RESULT_PREFIX}{task_id}"
            self.redis.setex(
                result_key,
                self.DEFAULT_TTL * 7,  # Keep results for 7 days
                json.dumps(result)
            )
        
        if status == TaskStatus.FAILED and error:
            task["error"] = error
            task["retry_count"] = task.get("retry_count", 0) + 1
        
        if status == TaskStatus.RETRYING:
            task["retry_count"] = task.get("retry_count", 0) + 1
        
        # Update task
        task_key = f"{self.TASK_PREFIX}{task_id}"
        self.redis.setex(
            task_key,
            self.DEFAULT_TTL,
            json.dumps(task)
        )
        
        return True
    
    def get_next_task(self, task_type: str) -> Optional[Dict[str, Any]]:
        """Get next task from queue (for worker processing).
        
        Args:
            task_type: Type of task to get
            
        Returns:
            Task dictionary or None if no tasks available
        """
        queue_key = f"{self.QUEUE_PREFIX}{task_type}"
        
        # Get highest priority task (highest score)
        # Use ZREVRANGE to get tasks in descending order of priority
        task_ids = self.redis.zrevrange(queue_key, 0, 0)
        
        if not task_ids:
            return None
        
        task_id = task_ids[0].decode() if isinstance(task_ids[0], bytes) else task_ids[0]
        task = self.get_task(task_id)
        
        if not task:
            # Task metadata missing, remove from queue
            self.redis.zrem(queue_key, task_id)
            return None
        
        # Check if task is delayed
        if task.get("delay_until"):
            delay_until = datetime.fromisoformat(task["delay_until"])
            if datetime.utcnow() < delay_until:
                # Task is still delayed, skip it
                return None
        
        # Update status to processing
        self.update_task_status(task_id, TaskStatus.PROCESSING)
        
        # Remove from queue (will be re-added if retry needed)
        self.redis.zrem(queue_key, task_id)
        
        return task
    
    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if retried, False if max retries exceeded
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        retry_count = task.get("retry_count", 0)
        max_retries = task.get("max_retries", 3)
        
        if retry_count >= max_retries:
            logger.warning(f"Task {task_id} exceeded max retries ({max_retries})")
            return False
        
        # Update status to retrying
        self.update_task_status(task_id, TaskStatus.RETRYING)
        
        # Re-add to queue with exponential backoff delay
        delay_seconds = 2 ** retry_count  # 1s, 2s, 4s, 8s, etc.
        task_type = task["type"]
        priority = task.get("priority", 0)
        
        queue_key = f"{self.QUEUE_PREFIX}{task_type}"
        score = (priority * 1000000) + ((datetime.utcnow().timestamp() + delay_seconds) * 1000)
        self.redis.zadd(queue_key, {task_id: score})
        
        logger.info(f"Task {task_id} retrying (attempt {retry_count + 1}/{max_retries}) with {delay_seconds}s delay")
        return True
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result dictionary or None if not found
        """
        result_key = f"{self.RESULT_PREFIX}{task_id}"
        result_data = self.redis.get(result_key)
        if result_data:
            return json.loads(result_data)
        return None
    
    def get_queue_stats(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """Get queue statistics.
        
        Args:
            task_type: Optional task type to filter by
            
        Returns:
            Dictionary with queue statistics
        """
        if task_type:
            queue_key = f"{self.QUEUE_PREFIX}{task_type}"
            pending_count = self.redis.zcard(queue_key)
            return {
                "task_type": task_type,
                "pending": pending_count,
            }
        else:
            # Get stats for all queues
            stats = {}
            pattern = f"{self.QUEUE_PREFIX}*"
            for key in self.redis.keys(pattern):
                task_type = key.decode().replace(self.QUEUE_PREFIX, "") if isinstance(key, bytes) else key.replace(self.QUEUE_PREFIX, "")
                queue_key = f"{self.QUEUE_PREFIX}{task_type}"
                pending_count = self.redis.zcard(queue_key)
                stats[task_type] = {"pending": pending_count}
            return stats


# Global instance
task_queue = TaskQueue()
