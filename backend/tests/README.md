# InTracker Backend Tests

## Test Setup

Tests use pytest with the following configuration:
- **Database**: Uses production database with transaction rollback for isolation
- **Fixtures**: Reusable test fixtures for users, teams, projects, features, todos
- **Coverage**: pytest-cov for code coverage reporting

## Running Tests

```bash
# Run all tests
docker-compose exec backend python -m pytest

# Run specific test file
docker-compose exec backend python -m pytest tests/services/test_project_service.py

# Run with coverage
docker-compose exec backend python -m pytest --cov=src --cov-report=html

# Run with verbose output
docker-compose exec backend python -m pytest -v
```

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── services/                # Service unit tests
│   ├── test_project_service.py
│   ├── test_feature_service.py
│   └── test_todo_service.py
└── README.md
```

## Test Fixtures

- `db`: Database session with transaction rollback
- `test_user`: Test user with unique email
- `test_admin_user`: Admin user with unique email
- `test_team`: Test team with unique name
- `test_project`: Test project
- `test_element`: Test project element
- `test_feature`: Test feature
- `test_todo`: Test todo

## Known Issues

Some tests may fail if service methods commit transactions, as this closes the transaction and prevents rollback. This is expected behavior and will be addressed in future refactoring to separate transaction management from service methods.

## Future Improvements

1. **Separate test database**: Use dedicated test database instead of production
2. **Service refactoring**: Move commit logic from services to controllers
3. **Mock services**: Use mocks for external dependencies
4. **Integration tests**: Add API endpoint integration tests
5. **Performance tests**: Add load and performance tests
