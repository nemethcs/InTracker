# Background Task Queue

## Overview

The InTracker backend includes a lightweight background task queue system for processing heavy operations asynchronously. This prevents blocking the main API thread and improves response times for users.

## Architecture

### Components

1. **TaskQueue** (`src/services/task_queue.py`): Redis-based task queue
   - Task enqueueing with priority support
   - Task status tracking
   - Retry logic with exponential backoff
   - Task result storage

2. **TaskWorker** (`src/services/task_worker.py`): Background worker
   - Processes tasks from the queue
   - Handles task execution and error handling
   - Automatic retry on failure
   - Pluggable task handlers

3. **Task Queue Controller** (`src/api/controllers/task_queue_controller.py`): API endpoints
   - Queue statistics
   - Task status monitoring

## Supported Task Types

Currently supported task types:
- `send_email`: Send generic email
- `send_invitation_email`: Send team invitation email
- `github_import_issues`: Import GitHub issues (placeholder)
- `github_import_milestones`: Import GitHub milestones (placeholder)

## Usage

### Enqueueing Tasks

```python
from src.services.task_queue import task_queue

# Enqueue an email task
task_id = task_queue.enqueue(
    task_type="send_email",
    task_data={
        "to_email": "user@example.com",
        "subject": "Welcome",
        "html_content": "<h1>Welcome!</h1>",
        "plain_text_content": "Welcome!",
    },
    priority=0,  # Higher = more priority
    max_retries=3,
    delay_seconds=0,  # Optional delay
)
```

### Checking Task Status

```python
# Get task status
task = task_queue.get_task(task_id)
print(f"Status: {task['status']}")  # pending, processing, completed, failed

# Get task result (if completed)
result = task_queue.get_task_result(task_id)
```

### API Endpoints

```bash
# Get queue statistics
GET /tasks/queue/stats?task_type=send_email

# Get task status
GET /tasks/{task_id}
```

## Task Status Flow

```
PENDING → PROCESSING → COMPLETED
              ↓
           FAILED → RETRYING → PROCESSING → ...
```

## Configuration

### Task Queue Settings

- **Default TTL**: 24 hours (task metadata)
- **Result TTL**: 7 days (task results)
- **Poll Interval**: 1 second (worker checks queue every second)
- **Max Retries**: 3 (default, configurable per task)

### Priority System

Tasks are processed in priority order:
- Higher priority = processed first
- Same priority = FIFO (first in, first out)
- Priority score: `(priority * 1000000) + timestamp`

## Retry Logic

Failed tasks are automatically retried with exponential backoff:
- Attempt 1: 1 second delay
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay
- Attempt 4: 8 seconds delay

After max retries exceeded, task is marked as permanently failed.

## Adding New Task Types

1. **Register handler in TaskWorker**:

```python
def _handle_my_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle my custom task."""
    # Your task logic here
    return {"success": True, "result": "..."}

# Register in __init__
self.register_handler("my_task", self._handle_my_task)
```

2. **Enqueue tasks**:

```python
task_id = task_queue.enqueue(
    task_type="my_task",
    task_data={"param1": "value1"},
)
```

## Worker Management

The task worker runs automatically when the backend starts:
- Started in `main.py` lifespan event
- Runs continuously in background
- Processes tasks for all registered task types
- Gracefully shuts down on application stop

## Monitoring

### Queue Statistics

```bash
curl http://localhost:3000/tasks/queue/stats
```

Returns:
```json
{
  "send_email": {"pending": 5},
  "github_import_issues": {"pending": 2}
}
```

### Task Status

```bash
curl http://localhost:3000/tasks/{task_id}
```

Returns:
```json
{
  "task": {
    "id": "...",
    "type": "send_email",
    "status": "completed",
    "created_at": "...",
    "updated_at": "..."
  },
  "result": {
    "success": true,
    "to_email": "user@example.com"
  }
}
```

## Future Improvements

Potential enhancements:
- [ ] Scheduled tasks (run at specific time)
- [ ] Task dependencies (task B waits for task A)
- [ ] Task progress tracking (for long-running tasks)
- [ ] Multiple workers (horizontal scaling)
- [ ] Task cancellation
- [ ] Task prioritization UI
- [ ] Migration to Celery (for advanced features)

## Migration from BackgroundTasks

Current code uses FastAPI `BackgroundTasks` for SignalR broadcasts. These are fine for lightweight operations. For heavy operations (email, GitHub imports), use the task queue:

**Before:**
```python
background_tasks.add_task(send_email, to_email, subject, content)
```

**After:**
```python
from src.services.task_queue import task_queue
task_id = task_queue.enqueue("send_email", {
    "to_email": to_email,
    "subject": subject,
    "html_content": content,
})
```

## Performance Considerations

- **Redis Required**: Task queue requires Redis to be running
- **Worker Overhead**: Worker polls queue every second (configurable)
- **Memory Usage**: Task metadata stored in Redis (24h TTL)
- **Concurrency**: Single worker processes one task at a time (can be scaled)

## Error Handling

- Tasks that fail are automatically retried
- After max retries, task is marked as failed
- Failed tasks are logged with error details
- Task results are stored separately for longer retention
