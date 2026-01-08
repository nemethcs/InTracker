# Refactoring Plan: rules_generator.py (636 lines)

## Current Structure Analysis

The `rules_generator.py` file contains 2 classes:

### 1. `RulesSection` (Lines ~8-44, ~45 lines)
- Represents a rules section with conditional inclusion
- `should_include()` method checks project conditions

### 2. `RulesGenerator` (Lines ~47-636, ~590 lines)
- Main class for generating cursor rules
- `_register_default_sections()` (~430 lines) - Very long method with many section definitions
- `generate_rules()` (~90 lines) - Generates final rules content
- Helper methods (~60 lines) - Various utility methods
- `add_custom_section()`, `update_section()` (~15 lines)

## Refactoring Strategy

Split into separate modules:

### 1. `rules_section.py` (~45 lines)
- `RulesSection` class

### 2. `rules_sections/` directory
- `__init__.py` - Exports all section creators
- `core_workflow_section.py` - Core workflow section
- `git_workflow_section.py` - Git workflow section
- `docker_section.py` - Docker section
- `mcp_server_section.py` - MCP server section
- `frontend_section.py` - Frontend section
- `github_section.py` - GitHub section
- `intracker_integration_section.py` - InTracker integration section
- `user_interaction_section.py` - User interaction section

### 3. `rules_generator.py` (refactored, ~200 lines)
- `RulesGenerator` class
- Imports section creators from `rules_sections/`
- `_register_default_sections()` calls section creators

## Implementation Steps

1. Create `rules_section.py` with `RulesSection` class
2. Create `rules_sections/` directory
3. Create section creator modules
4. Refactor `RulesGenerator` to use section creators
5. Test all functionality

## Dependencies

All modules will share:
- `RulesSection` from `rules_section.py`
- `Project` model from `src.database.models`
