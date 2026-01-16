# OpenAPI/Swagger Documentation

## Overview

The InTracker API uses FastAPI's automatic OpenAPI/Swagger documentation generation. The API documentation is available at:

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`
- **OpenAPI JSON**: `http://localhost:3000/openapi.json`

## Documentation Features

### Automatic Generation

FastAPI automatically generates OpenAPI documentation from:
- **Route decorators**: `@router.get()`, `@router.post()`, etc.
- **Pydantic schemas**: Request and response models
- **Type hints**: Parameter types and return types
- **Docstrings**: Endpoint descriptions

### Current Documentation Status

✅ **Well Documented:**
- Request/response schemas (Pydantic models)
- Parameter types and validation
- Basic endpoint descriptions
- Authentication requirements

⚠️ **Needs Improvement:**
- Detailed endpoint descriptions
- Request/response examples
- Error response documentation
- Response status codes documentation

## Best Practices

### 1. Endpoint Descriptions

Always include detailed docstrings for endpoints:

```python
@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new project.
    
    Creates a new project in the system. The project will be owned by the team
    specified in `team_id`. The user must be a member of that team.
    
    **Required fields:**
    - `name`: Project name (1-255 characters)
    - `team_id`: UUID of the team that will own the project
    
    **Optional fields:**
    - `description`: Project description
    - `status`: Project status (default: "active")
    - `tags`: List of tags for categorization
    - `technology_tags`: List of technology tags
    - `cursor_instructions`: Instructions for Cursor AI agent
    - `github_repo_url`: GitHub repository URL
    - `github_repo_id`: GitHub repository ID
    
    **Returns:**
    - `201 Created`: Project created successfully
    - `400 Bad Request`: Invalid input data
    - `403 Forbidden`: User is not a member of the team
    - `404 Not Found`: Team not found
    
    **Example:**
    ```json
    {
      "name": "My Project",
      "team_id": "123e4567-e89b-12d3-a456-426614174000",
      "description": "A new project",
      "status": "active"
    }
    ```
    """
```

### 2. Schema Examples

Add examples to Pydantic schemas:

```python
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    team_id: UUID = Field(..., description="Team ID that will own this project")
    description: Optional[str] = Field(None, description="Project description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Project",
                "team_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "A new project",
                "status": "active"
            }
        }
```

### 3. Response Status Codes

Document all possible response status codes:

```python
@router.post("/projects", 
    response_model=ProjectResponse, 
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Project created successfully"},
        400: {"description": "Invalid input data"},
        403: {"description": "User is not a member of the team"},
        404: {"description": "Team not found"},
    }
)
```

### 4. Error Responses

Document error responses:

```python
@router.post("/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid project name"
                    }
                }
            }
        },
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You are not a member of this team"
                    }
                }
            }
        },
    }
)
```

### 5. Query Parameters

Document query parameters with descriptions:

```python
@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    team_id: Optional[UUID] = Query(None, description="Filter by team ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List projects with pagination.
    
    Returns a paginated list of projects accessible to the current user.
    Admins can see all projects, regular users only see projects from their teams.
    
    **Query Parameters:**
    - `page`: Page number (default: 1, minimum: 1)
    - `page_size`: Number of items per page (default: 20, minimum: 1, maximum: 100)
    - `status`: Filter by project status (optional)
    - `team_id`: Filter by team ID (optional)
    
    **Returns:**
    - `200 OK`: List of projects with pagination metadata
    """
```

## OpenAPI Tags

Tags are used to group endpoints in the Swagger UI. Tags are defined in `main.py`:

```python
openapi_tags=[
    {
        "name": "projects",
        "description": "Project management endpoints for creating, updating, and managing projects.",
    },
    # ... more tags
]
```

## Security Schemes

Authentication is documented using OpenAPI security schemes:

```python
# In main.py or router definition
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/projects", dependencies=[Depends(security)])
async def create_project(...):
    ...
```

## Customizing OpenAPI Schema

To customize the OpenAPI schema, use FastAPI's `openapi_schema` customization:

```python
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="InTracker API",
        version="0.1.0",
        description="AI-first project management system API",
        routes=app.routes,
    )
    # Customize schema here
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## Testing Documentation

1. **Start the backend**: `docker-compose up backend`
2. **Open Swagger UI**: `http://localhost:3000/docs`
3. **Test endpoints**: Use the "Try it out" feature
4. **Check examples**: Verify request/response examples are correct

## Future Improvements

- [ ] Add detailed examples to all endpoints
- [ ] Document all error responses
- [ ] Add response status code documentation
- [ ] Add request/response examples to schemas
- [ ] Document authentication flow
- [ ] Add API versioning documentation
- [ ] Document rate limiting (when implemented)
- [ ] Add webhook documentation
