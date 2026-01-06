"""Import database models from backend."""
# Import models from backend to avoid duplication
import sys
from pathlib import Path
import importlib.util
import os

# Try multiple paths for backend (Docker first, then local dev)
possible_paths = [
    Path("/backend/src"),  # Docker volume mount (preferred)
    Path(__file__).parent.parent.parent / "backend" / "src",  # Local dev
]

backend_src_path = None
for path in possible_paths:
    if path.exists() and (path / "database" / "base.py").exists():
        backend_src_path = path
        break

if not backend_src_path:
    raise ImportError("Could not find backend/src directory. Checked paths: " + str(possible_paths))

# Add backend/src to path so we can import src.database.models
if str(backend_src_path) not in sys.path:
    sys.path.insert(0, str(backend_src_path))

# Import base first
base_path = backend_src_path / "database" / "base.py"
if not base_path.exists():
    raise ImportError(f"Backend base.py not found at {base_path}")

base_spec = importlib.util.spec_from_file_location("src.database.base", base_path)
base_module = importlib.util.module_from_spec(base_spec)
sys.modules["src.database.base"] = base_module
sys.modules["src.database"] = type(sys)("src.database")
sys.modules["src.database"].base = base_module
base_spec.loader.exec_module(base_module)

# Now import models
models_path = backend_src_path / "database" / "models.py"
if not models_path.exists():
    raise ImportError(f"Backend models.py not found at {models_path}")

models_spec = importlib.util.spec_from_file_location("src.database.models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
sys.modules["src.database.models"] = models_module
models_spec.loader.exec_module(models_module)

# Export models
User = models_module.User
Project = models_module.Project
ProjectElement = models_module.ProjectElement
Feature = models_module.Feature
Todo = models_module.Todo
Session = models_module.Session
Document = models_module.Document
GitHubBranch = models_module.GitHubBranch
ElementDependency = models_module.ElementDependency
FeatureElement = models_module.FeatureElement
UserProject = models_module.UserProject
Idea = models_module.Idea
GitHubSync = models_module.GitHubSync

__all__ = [
    "User",
    "Project",
    "ProjectElement",
    "Feature",
    "Todo",
    "Session",
    "Document",
    "GitHubBranch",
    "ElementDependency",
    "FeatureElement",
    "UserProject",
    "Idea",
    "GitHubSync",
]
