# MCP Tools Analysis Report

## Overview
Total: **52 tools** across 8 categories

## Tool Categories Breakdown

### 1. Project Tools (9 tools) ✅ TESTED
1. `mcp_get_project_context` - Get comprehensive project information
2. `mcp_get_resume_context` - Get resume context (Last/Now/Blockers/Constraints)
3. `mcp_get_project_structure` - Get hierarchical element tree
4. `mcp_get_active_todos` - Get active todos with filters
5. `mcp_create_project` - Create new project
6. `mcp_list_projects` - List projects with filters
7. `mcp_update_project` - Update project
8. `mcp_identify_project_by_path` - Identify project by working directory
9. `mcp_load_cursor_rules` - Load cursor rules from project

**Test Results:**
- ✅ All tools work correctly
- ✅ `get_project_context` already includes structure, making `get_project_structure` redundant
- ✅ `get_resume_context` is essential for Cursor workflow (Last/Now/Blockers/Constraints)
- ✅ `get_active_todos` is essential for workflow
- ✅ `identify_project_by_path` is essential for project auto-detection

**Analysis:**
- **Essential (7)**: get_project_context, get_resume_context, get_active_todos, create_project, list_projects, identify_project_by_path, load_cursor_rules
- **Optional/Redundant (2)**: 
  - `get_project_structure` - **REDUNDANT** (already in get_project_context)
  - `update_project` - **OPTIONAL** (rarely needed in Cursor workflow)

### 2. Feature Tools (7 tools)
1. `mcp_create_feature` - Create feature and link elements
2. `mcp_get_feature` - Get feature with todos and elements
3. `mcp_list_features` - List features with filters
4. `mcp_update_feature_status` - Update status and recalculate progress
5. `mcp_get_feature_todos` - Get todos for feature
6. `mcp_get_feature_elements` - Get elements linked to feature
7. `mcp_link_element_to_feature` - Link element to feature

**Analysis:**
- **Essential (5)**: create_feature, get_feature, list_features, update_feature_status, link_element_to_feature
- **Optional (2)**: get_feature_todos (can use get_feature), get_feature_elements (can use get_feature)

### 3. Todo Tools (5 tools)
1. `mcp_create_todo` - Create todo and link to feature
2. `mcp_update_todo_status` - Update status with optimistic locking
3. `mcp_list_todos` - List todos with filters
4. `mcp_assign_todo` - Assign todo to user
5. `mcp_link_todo_to_feature` - Link todo to feature

**Analysis:**
- **Essential (5)**: All tools are essential for todo management workflow

### 4. Session Tools (3 tools)
1. `mcp_start_session` - Start work session
2. `mcp_update_session` - Update session with completed items
3. `mcp_end_session` - End session and generate summary

**Analysis:**
- **Essential (3)**: All tools are essential for session tracking

### 5. Document Tools (3 tools)
1. `mcp_get_document` - Get document content
2. `mcp_list_documents` - List documents for project
3. `mcp_create_document` - Create document

**Analysis:**
- **Essential (2)**: get_document, create_document
- **Optional (1)**: list_documents (can be in project context)

### 6. GitHub Tools (16 tools) ⚠️ LARGEST CATEGORY
1. `mcp_get_branches` - Get branches for project or feature
2. `mcp_connect_github_repo` - Connect GitHub repository
3. `mcp_get_repo_info` - Get repository information
4. `mcp_link_element_to_issue` - Link element to GitHub issue
5. `mcp_get_github_issue` - Get GitHub issue information
6. `mcp_create_github_issue` - Create GitHub issue
7. `mcp_link_todo_to_pr` - Link todo to GitHub PR
8. `mcp_get_github_pr` - Get GitHub PR information
9. `mcp_create_github_pr` - Create GitHub PR
10. `mcp_create_branch_for_feature` - Create branch for feature
11. `mcp_get_active_branch` - Get active branch from working directory
12. `mcp_link_branch_to_feature` - Link branch to feature
13. `mcp_get_feature_branches` - Get branches for feature
14. `mcp_get_branch_status` - Get branch status (ahead/behind, conflicts)
15. `mcp_get_commits_for_feature` - Get commits for feature
16. `mcp_parse_commit_message` - Parse commit message for metadata

**Analysis:**
- **Essential (6)**: connect_github_repo, get_repo_info, create_github_issue, create_github_pr, create_branch_for_feature, get_active_branch
- **Optional (10)**: Many tools could be consolidated or made optional:
  - Branch tools: get_branches, get_feature_branches, get_branch_status could be combined
  - Issue tools: get_github_issue, link_element_to_issue could be optional
  - PR tools: get_github_pr, link_todo_to_pr could be optional
  - Commit tools: get_commits_for_feature, parse_commit_message could be optional

### 7. Idea Tools (5 tools)
1. `mcp_create_idea` - Create new idea
2. `mcp_list_ideas` - List ideas with filters
3. `mcp_get_idea` - Get idea by ID
4. `mcp_update_idea` - Update idea
5. `mcp_convert_idea_to_project` - Convert idea to project

**Analysis:**
- **Essential (2)**: create_idea, convert_idea_to_project
- **Optional (3)**: list_ideas, get_idea, update_idea (could be optional for Cursor workflow)

### 8. Import Tools (4 tools)
1. `mcp_parse_file_structure` - Parse project file structure
2. `mcp_import_github_issues` - Import GitHub issues as todos
3. `mcp_import_github_milestones` - Import GitHub milestones as features
4. `mcp_analyze_codebase` - Analyze codebase and suggest structure

**Analysis:**
- **Essential (2)**: import_github_issues, import_github_milestones (for migration)
- **Optional (2)**: parse_file_structure, analyze_codebase (one-time setup tools)

## Summary

### Essential Tools: ~35-40
### Optional Tools: ~12-17

## Recommendations

1. **GitHub Tools Consolidation**: The 16 GitHub tools could be reduced to ~8-10 by:
   - Combining branch-related tools into one `mcp_manage_branches` tool
   - Making read-only tools (get_github_issue, get_github_pr) optional
   - Combining commit-related tools

2. **Feature Tools**: `get_feature_todos` and `get_feature_elements` could be removed if `get_feature` already returns this data

3. **Project Tools**: `get_project_structure` could be optional if included in `get_project_context`

4. **Idea Tools**: Most idea tools could be optional for the core Cursor workflow

5. **Import Tools**: `parse_file_structure` and `analyze_codebase` are one-time setup tools, could be optional

## Next Steps
1. Test each tool category
2. Verify which tools are actually used in practice
3. Create consolidation plan
4. Implement tool reduction if needed
