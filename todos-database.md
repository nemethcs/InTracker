# InTracker - Database Fejlesztési Todo Lista

## Fázis 1: Alapvető Séma (MVP)

### 1.1. Core Tables

- [x] **Users table**
  - [x] id (UUID, PRIMARY KEY)
  - [x] email (TEXT, UNIQUE, NOT NULL)
  - [x] name (TEXT)
  - [x] password_hash (TEXT, NOT NULL)
  - [x] github_username (TEXT)
  - [x] avatar_url (TEXT)
  - [x] is_active (BOOLEAN, DEFAULT TRUE)
  - [x] last_login_at (TIMESTAMP)
  - [x] created_at (TIMESTAMP, DEFAULT NOW())
  - [x] updated_at (TIMESTAMP, DEFAULT NOW())
  - [x] Index: idx_users_email

- [x] **Projects table**
  - [x] id (UUID, PRIMARY KEY)
  - [x] name (TEXT, NOT NULL)
  - [x] description (TEXT)
  - [x] status (TEXT, CHECK: active/paused/blocked/completed/archived)
  - [x] tags (TEXT[])
  - [x] technology_tags (TEXT[])
  - [x] created_at (TIMESTAMP, DEFAULT NOW())
  - [x] updated_at (TIMESTAMP, DEFAULT NOW())
  - [x] last_session_at (TIMESTAMP)
  - [x] resume_context (JSONB)
  - [x] cursor_instructions (TEXT)
  - [x] github_repo_url (TEXT)
  - [x] github_repo_id (TEXT)
  - [x] metadata (JSONB)
  - [x] Index: idx_projects_status

- [x] **User_Projects table**
  - [x] user_id (UUID, FK → users.id)
  - [x] project_id (UUID, FK → projects.id)
  - [x] role (TEXT, CHECK: owner/editor/viewer)
  - [x] created_at (TIMESTAMP, DEFAULT NOW())
  - [x] PRIMARY KEY (user_id, project_id)
  - [x] Index: idx_user_projects_user
  - [x] Index: idx_user_projects_project

- [x] **Project_Elements table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] project_id (UUID, FK → projects.id, CASCADE DELETE)
  - [ ] parent_id (UUID, FK → project_elements.id, CASCADE DELETE)
  - [ ] type (TEXT, CHECK: module/feature/component/milestone/technical_block/decision_point)
  - [ ] title (TEXT, NOT NULL)
  - [ ] description (TEXT)
  - [ ] status (TEXT, CHECK: todo/in_progress/blocked/done)
  - [ ] position (INTEGER)
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] updated_at (TIMESTAMP, DEFAULT NOW())
  - [ ] definition_of_done (TEXT)
  - [ ] github_issue_number (INTEGER)
  - [ ] github_issue_url (TEXT)
  - [ ] metadata (JSONB)
  - [x] Index: idx_project_elements_project
  - [x] Index: idx_project_elements_parent
  - [x] Index: idx_project_elements_status

- [x] **Features table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] project_id (UUID, FK → projects.id, CASCADE DELETE)
  - [ ] name (TEXT, NOT NULL)
  - [ ] description (TEXT)
  - [ ] status (TEXT, CHECK: todo/in_progress/blocked/done)
  - [ ] progress_percentage (INTEGER, DEFAULT 0)
  - [ ] total_todos (INTEGER, DEFAULT 0)
  - [ ] completed_todos (INTEGER, DEFAULT 0)
  - [ ] assigned_to (UUID, FK → users.id)
  - [ ] created_by (UUID, FK → users.id)
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] updated_at (TIMESTAMP, DEFAULT NOW())
  - [ ] metadata (JSONB)
  - [x] Index: idx_features_project
  - [x] Index: idx_features_status
  - [x] Index: idx_features_assigned

- [x] **Todos table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] element_id (UUID, FK → project_elements.id, CASCADE DELETE)
  - [ ] feature_id (UUID, FK → features.id, SET NULL)
  - [ ] title (TEXT, NOT NULL)
  - [ ] description (TEXT)
  - [ ] status (TEXT, CHECK: todo/in_progress/blocked/done)
  - [ ] position (INTEGER)
  - [ ] estimated_effort (INTEGER)
  - [ ] blocker_reason (TEXT)
  - [ ] assigned_to (UUID, FK → users.id)
  - [ ] created_by (UUID, FK → users.id)
  - [ ] version (INTEGER, DEFAULT 1) // Optimistic locking
  - [ ] github_issue_number (INTEGER)
  - [ ] github_pr_number (INTEGER)
  - [ ] github_pr_url (TEXT)
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] updated_at (TIMESTAMP, DEFAULT NOW())
  - [ ] completed_at (TIMESTAMP)
  - [ ] metadata (JSONB)
  - [x] Index: idx_todos_element
  - [x] Index: idx_todos_feature
  - [x] Index: idx_todos_status
  - [x] Index: idx_todos_assigned
  - [x] Index: idx_todos_created_by

- [x] **Feature_Elements table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] feature_id (UUID, FK → features.id, CASCADE DELETE)
  - [ ] element_id (UUID, FK → project_elements.id, CASCADE DELETE)
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] UNIQUE (feature_id, element_id)
  - [x] Index: idx_feature_elements_feature
  - [x] Index: idx_feature_elements_element

- [x] **Element_Dependencies table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] element_id (UUID, FK → project_elements.id, CASCADE DELETE)
  - [ ] depends_on_element_id (UUID, FK → project_elements.id, CASCADE DELETE)
  - [ ] dependency_type (TEXT, CHECK: blocks/requires/related)
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] UNIQUE (element_id, depends_on_element_id)
  - [x] Index: idx_dependencies_element
  - [x] Index: idx_dependencies_depends_on

- [x] **Documents table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] project_id (UUID, FK → projects.id, CASCADE DELETE)
  - [ ] element_id (UUID, FK → project_elements.id, SET NULL)
  - [ ] type (TEXT, CHECK: architecture/adr/domain/constraints/runbook/ai_instructions)
  - [ ] title (TEXT, NOT NULL)
  - [ ] content (TEXT, NOT NULL) // Markdown
  - [ ] tags (TEXT[])
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] updated_at (TIMESTAMP, DEFAULT NOW())
  - [ ] version (INTEGER, DEFAULT 1)
  - [ ] metadata (JSONB)
  - [x] Index: idx_documents_project
  - [x] Index: idx_documents_element
  - [x] Index: idx_documents_type

- [x] **Sessions table**
  - [x] id (UUID, PRIMARY KEY)
  - [x] project_id (UUID, FK → projects.id, CASCADE DELETE)
  - [x] user_id (UUID, FK → users.id)
  - [x] title (TEXT)
  - [x] goal (TEXT)
  - [x] started_at (TIMESTAMP, DEFAULT NOW())
  - [x] ended_at (TIMESTAMP)
  - [x] summary (TEXT)
  - [x] feature_ids (UUID[], FK → features.id)
  - [x] todos_completed (UUID[], FK → todos.id)
  - [x] features_completed (UUID[], FK → features.id)
  - [x] elements_updated (UUID[], FK → project_elements.id)
  - [x] notes (TEXT)
  - [x] metadata (JSONB)
  - [x] Index: idx_sessions_project
  - [x] Index: idx_sessions_user
  - [x] Index: idx_sessions_started

- [x] **Ideas table**
  - [x] id (UUID, PRIMARY KEY)
  - [x] title (TEXT, NOT NULL)
  - [x] description (TEXT)
  - [x] status (TEXT, CHECK: draft/active/archived)
  - [x] tags (TEXT[])
  - [x] created_at (TIMESTAMP, DEFAULT NOW())
  - [x] updated_at (TIMESTAMP, DEFAULT NOW())
  - [x] converted_to_project_id (UUID, FK → projects.id)
  - [x] metadata (JSONB)
  - [x] Index: idx_ideas_status

### 1.2. GitHub Integration Tables

- [x] **GitHub_Branches table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] project_id (UUID, FK → projects.id, CASCADE DELETE)
  - [ ] feature_id (UUID, FK → features.id, SET NULL)
  - [ ] branch_name (TEXT, NOT NULL)
  - [ ] base_branch (TEXT, DEFAULT 'main')
  - [ ] status (TEXT, CHECK: active/merged/deleted)
  - [ ] ahead_count (INTEGER, DEFAULT 0)
  - [ ] behind_count (INTEGER, DEFAULT 0)
  - [ ] has_conflicts (BOOLEAN, DEFAULT FALSE)
  - [ ] last_commit_sha (TEXT)
  - [ ] last_commit_message (TEXT)
  - [ ] created_at (TIMESTAMP, DEFAULT NOW())
  - [ ] updated_at (TIMESTAMP, DEFAULT NOW())
  - [ ] merged_at (TIMESTAMP)
  - [ ] UNIQUE (project_id, branch_name)
  - [x] Index: idx_branches_project
  - [x] Index: idx_branches_feature
  - [x] Index: idx_branches_status

- [x] **GitHub_Sync table**
  - [ ] id (UUID, PRIMARY KEY)
  - [ ] project_id (UUID, FK → projects.id, CASCADE DELETE)
  - [ ] entity_type (TEXT, CHECK: element/todo/feature/branch)
  - [ ] entity_id (UUID, NOT NULL)
  - [ ] github_type (TEXT, CHECK: issue/pr/branch/commit)
  - [ ] github_id (INTEGER) // NULL lehet commit SHA esetén
  - [ ] github_url (TEXT)
  - [ ] last_synced_at (TIMESTAMP, DEFAULT NOW())
  - [ ] sync_direction (TEXT, CHECK: tracker_to_github/github_to_tracker/bidirectional)
  - [ ] UNIQUE (entity_id, github_type, github_id)
  - [ ] Index: idx_github_sync_project
  - [ ] Index: idx_github_sync_entity

## Fázis 2: Migrations és Constraints

- [x] **Prisma Schema létrehozása**
  - [x] schema.prisma fájl
  - [x] Model definíciók
  - [x] Relations definiálása
  - [x] Indexek definiálása

- [x] **Initial Migration**
  - [x] `prisma migrate dev --name init`
  - [x] Migration fájl ellenőrzése
  - [ ] Rollback tesztelése

- [ ] **Foreign Key Constraints**
  - [ ] CASCADE DELETE tesztelése
  - [ ] SET NULL tesztelése
  - [ ] Constraint nevek definiálása

- [ ] **Check Constraints**
  - [ ] Status enum értékek validálása
  - [ ] Role enum értékek validálása
  - [ ] Type enum értékek validálása

- [ ] **Unique Constraints**
  - [ ] Email unique constraint
  - [ ] User-Project unique constraint
  - [ ] Branch name unique constraint
  - [ ] GitHub sync unique constraint

## Fázis 3: Functions és Triggers

- [ ] **Auto-update timestamps trigger**
  - [ ] updated_at automatikus frissítés
  - [ ] Minden táblán implementálás

- [ ] **Feature progress calculation function**
  - [ ] Function: calculate_feature_progress(feature_id)
  - [ ] Trigger: On todo status change → update feature progress
  - [ ] Trigger: On todo create/delete → update feature total_todos

- [ ] **Project last_session_at update trigger**
  - [ ] On session end → update project.last_session_at

- [ ] **Version increment trigger (Optimistic locking)**
  - [ ] On todo update → version++
  - [ ] On feature update → version++

## Fázis 4: Views és Materialized Views

- [ ] **User Projects View**
  - [ ] View: user_projects_with_roles
  - [ ] User + Project + Role összekapcsolás

- [ ] **Project Statistics View**
  - [ ] View: project_statistics
  - [ ] Todo count, feature count, completion rate

- [ ] **User Activity View**
  - [ ] View: user_activity_summary
  - [ ] Last session, active todos, assigned features

- [ ] **Team Dashboard View**
  - [ ] Materialized View: team_dashboard_data
  - [ ] Refresh strategy (cron job)

## Fázis 5: Indexek Optimalizálás

- [ ] **Query performance analysis**
  - [ ] EXPLAIN ANALYZE futtatása
  - [ ] Slow query identification

- [ ] **Composite Indexek**
  - [ ] Index: (project_id, status) on todos
  - [ ] Index: (feature_id, status) on todos
  - [ ] Index: (user_id, project_id) on user_projects
  - [ ] Index: (assigned_to, status) on todos

- [ ] **Partial Indexek**
  - [ ] Index: WHERE status = 'in_progress' on todos
  - [ ] Index: WHERE is_active = TRUE on users

## Fázis 6: Seed Data és Testing

- [ ] **Seed script létrehozása**
  - [ ] Test users (3-5 user)
  - [ ] Test projects (2-3 project)
  - [ ] Test features, todos, elements
  - [ ] Test relationships

- [ ] **Test data cleanup**
  - [ ] Seed data törlés script
  - [ ] Reset database script

- [ ] **Performance testing**
  - [ ] Load testing (1000+ todos)
  - [ ] Concurrent access testing
  - [ ] Query performance benchmarking

## Fázis 7: Backup és Recovery

- [ ] **Backup stratégia**
  - [ ] Daily automated backups
  - [ ] Backup retention policy (7 nap)
  - [ ] Backup testing

- [ ] **Recovery testing**
  - [ ] Point-in-time recovery teszt
  - [ ] Database restore procedure

## Fázis 8: Monitoring és Maintenance

- [ ] **Query logging**
  - [ ] Slow query log enable
  - [ ] Query performance monitoring

- [ ] **Database maintenance**
  - [ ] VACUUM schedule
  - [ ] ANALYZE schedule
  - [ ] Index maintenance

- [ ] **Connection pooling**
  - [ ] PgBouncer konfiguráció
  - [ ] Connection limit settings

---

## Prioritások

**MVP (Minimum Viable Product):**
1. Core tables (Users, Projects, User_Projects, Project_Elements, Features, Todos)
2. Basic indexes
3. Foreign key constraints
4. Initial migration

**Fázis 1 után:**
5. GitHub integration tables
6. Functions és triggers
7. Views
8. Seed data

**Production előtt:**
9. Performance optimization
10. Backup stratégia
11. Monitoring setup
