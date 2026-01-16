"""Background task worker for processing queued tasks.

This worker processes tasks from the task queue in the background.
It should be run as a separate process or asyncio task.
"""
import asyncio
import logging
import json
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from src.services.task_queue import TaskQueue, TaskStatus
from src.services.email_service import email_service
from src.services.github_service import GitHubService
from src.database.base import SessionLocal

logger = logging.getLogger(__name__)


class TaskWorker:
    """Background task worker for processing queued tasks."""
    
    def __init__(self, task_queue: TaskQueue):
        """Initialize task worker.
        
        Args:
            task_queue: TaskQueue instance
        """
        self.task_queue = task_queue
        self.running = False
        self.task_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default task handlers."""
        self.register_handler("send_email", self._handle_send_email)
        self.register_handler("send_invitation_email", self._handle_send_invitation_email)
        self.register_handler("github_import_issues", self._handle_github_import_issues)
        self.register_handler("github_import_milestones", self._handle_github_import_milestones)
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a task handler.
        
        Args:
            task_type: Type of task
            handler: Handler function that takes (task_data: Dict) -> Dict
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def process_task(self, task: Dict[str, Any]) -> bool:
        """Process a single task.
        
        Args:
            task: Task dictionary
            
        Returns:
            True if task processed successfully, False otherwise
        """
        task_id = task["id"]
        task_type = task["type"]
        task_data = task["data"]
        
        logger.info(f"Processing task {task_id} of type {task_type}")
        
        try:
            # Get handler
            handler = self.task_handlers.get(task_type)
            if not handler:
                error_msg = f"No handler registered for task type: {task_type}"
                logger.error(error_msg)
                self.task_queue.update_task_status(task_id, TaskStatus.FAILED, error=error_msg)
                return False
            
            # Execute handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(task_data)
            else:
                # Run sync handler in thread pool
                result = await asyncio.to_thread(handler, task_data)
            
            # Update task status
            self.task_queue.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
            logger.info(f"Task {task_id} completed successfully")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task {task_id} failed: {error_msg}", exc_info=True)
            self.task_queue.update_task_status(task_id, TaskStatus.FAILED, error=error_msg)
            
            # Retry if retries available
            if self.task_queue.retry_task(task_id):
                logger.info(f"Task {task_id} will be retried")
            else:
                logger.error(f"Task {task_id} failed permanently after max retries")
            
            return False
    
    async def run(self, poll_interval: float = 1.0):
        """Run the worker (processes tasks continuously).
        
        Args:
            poll_interval: Seconds to wait between queue polls (default: 1.0)
        """
        self.running = True
        logger.info("Task worker started")
        
        while self.running:
            try:
                # Process tasks for each registered task type
                for task_type in self.task_handlers.keys():
                    task = self.task_queue.get_next_task(task_type)
                    if task:
                        await self.process_task(task)
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error in task worker: {e}", exc_info=True)
                await asyncio.sleep(poll_interval)
        
        logger.info("Task worker stopped")
    
    def stop(self):
        """Stop the worker."""
        self.running = False
    
    # Task handlers
    
    def _handle_send_email(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send_email task.
        
        Args:
            task_data: Task data with to_email, subject, html_content, plain_text_content
            
        Returns:
            Result dictionary
        """
        to_email = task_data["to_email"]
        subject = task_data["subject"]
        html_content = task_data["html_content"]
        plain_text_content = task_data.get("plain_text_content")
        
        success = email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content,
        )
        
        return {
            "success": success,
            "to_email": to_email,
            "subject": subject,
        }
    
    def _handle_send_invitation_email(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send_invitation_email task.
        
        Args:
            task_data: Task data with to_email, invitation_code, team_name, etc.
            
        Returns:
            Result dictionary
        """
        to_email = task_data["to_email"]
        invitation_code = task_data["invitation_code"]
        team_name = task_data["team_name"]
        inviter_name = task_data.get("inviter_name")
        expires_in_days = task_data.get("expires_in_days")
        
        success = email_service.send_invitation_email(
            to_email=to_email,
            invitation_code=invitation_code,
            team_name=team_name,
            inviter_name=inviter_name,
            expires_in_days=expires_in_days,
        )
        
        return {
            "success": success,
            "to_email": to_email,
            "invitation_code": invitation_code,
        }
    
    def _handle_github_import_issues(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle github_import_issues task.
        
        Args:
            task_data: Task data with project_id, user_id, etc.
            
        Returns:
            Result dictionary
        """
        # This is a placeholder - actual implementation would use MCP import tools
        # For now, just log that it would be processed
        logger.info(f"GitHub import issues task would be processed: {task_data}")
        return {
            "success": True,
            "message": "GitHub import issues task queued (implementation pending)",
        }
    
    def _handle_github_import_milestones(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle github_import_milestones task.
        
        Args:
            task_data: Task data with project_id, user_id, etc.
            
        Returns:
            Result dictionary
        """
        # This is a placeholder - actual implementation would use MCP import tools
        logger.info(f"GitHub import milestones task would be processed: {task_data}")
        return {
            "success": True,
            "message": "GitHub import milestones task queued (implementation pending)",
        }


# Global worker instance (will be started in main.py)
task_worker: Optional[TaskWorker] = None
