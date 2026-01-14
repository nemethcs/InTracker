import { useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Play, 
  Copy, 
  Check, 
  ChevronRight, 
  Terminal, 
  Code, 
  GitBranch,
  CheckCircle2,
  AlertCircle,
  Lightbulb,
  Rocket,
  BookOpen
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface GuideSection {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  color: string
  steps: GuideStep[]
}

interface GuideStep {
  title: string
  description: string
  type: 'cursor' | 'terminal' | 'info'
  command?: string
  deeplink?: string
  code?: string
  tips?: string[]
  warning?: string
}

// Helper function to generate Cursor deeplinks
const generateCursorDeeplink = (promptText: string): string => {
  return `cursor://anysphere.cursor-deeplink/prompt?text=${encodeURIComponent(promptText)}`
}

// Helper function to generate Cursor rule deeplinks
const generateRuleDeeplink = (ruleName: string, ruleContent: string): string => {
  return `cursor://anysphere.cursor-deeplink/rule?name=${encodeURIComponent(ruleName)}&text=${encodeURIComponent(ruleContent)}`
}

// Base InTracker workflow rules content
const INTracker_BASE_RULES = `# InTracker Workflow Rules

## 🚨 MANDATORY: Session Start Workflow

**EVERY session MUST start with:**

1. **Enforce Workflow (MANDATORY!):**
   - Use \`mcp_enforce_workflow()\` tool at the START of EVERY session
   - This automatically:
     - Identifies the project
     - Loads resume context (Last/Now/Blockers/Constraints)
     - Loads cursor rules
     - Returns workflow checklist

2. **Resume Context:**
   - Get resume context: \`mcp_get_resume_context(projectId)\`
   - Shows: Last session, next todos, active elements, blockers, constraints

3. **Load Cursor Rules (first time only):**
   - Load cursor rules: \`mcp_load_cursor_rules(projectId)\`
   - Rules are saved to \`.cursor/rules/intracker-project-rules.mdc\`

## 🚨 CRITICAL: Branch Check (MANDATORY for feature work!)

**ALWAYS check branch before starting work on a feature!**

- Check current branch: \`git branch --show-current\`
- If working on a feature:
  - Get feature: \`mcp_get_feature(featureId)\`
  - Get feature branches: \`mcp_get_feature_branches(featureId)\`
  - If feature branch exists: \`git checkout feature/{feature-name}\` then \`git pull origin feature/{feature-name}\`
  - If NO feature branch: \`mcp_create_branch_for_feature(featureId)\` then \`git checkout feature/{feature-name}\`
- If NOT working on a feature: Use \`develop\` branch
- **NEVER start working on a feature without checking the branch first!**

## Todo Status Workflow

**Todo statuses:** \`new\` → \`in_progress\` → \`tested\` → \`done\`

1. **Start work:** \`mcp_update_todo_status(todoId, "in_progress", expectedVersion)\`
2. **After testing:** \`mcp_update_todo_status(todoId, "tested", expectedVersion)\` (only if tested!)
3. **After merge to dev:** \`mcp_update_todo_status(todoId, "done", expectedVersion)\` (only after tested AND merged!)

**CRITICAL:**
- Use \`expectedVersion\` for optimistic locking
- Only mark as \`tested\` if you actually tested it!
- Only mark as \`done\` if tested AND merged to dev branch!

## Git Workflow (MANDATORY - Follow this order!)

**🚨 Before starting work - BRANCH CHECK (MANDATORY!):**
- ALWAYS check branch before starting work on a feature!
- See "Branch Check" section above

**During work:**
- Make code changes
- Test your changes
- Check for errors: \`read_lints\` tool
- Fix any issues

**Before committing:**
- Check git status: \`git status\`
- Review changes: \`git diff\`
- Stage all changes: \`git add -A\`
- Verify staged changes: \`git status\`

**Commit (MANDATORY format):**
- Format: \`{type}({scope}): {description} [feature:{featureId}]\`
- Types: \`feat\`, \`fix\`, \`refactor\`, \`docs\`, \`test\`, \`chore\`
- Include completed todos in commit message body:
  \`\`\`
  {type}({scope}): {description} [feature:{featureId}]
  
  - [x] Todo item 1
  - [x] Todo item 2
  \`\`\`

**After committing:**
- Push to remote: \`git push origin {branch-name}\`
- Update todo status to \`tested\`: \`mcp_update_todo_status(todoId, "tested")\` (only if tested!)
- Link todo to PR if PR exists: \`mcp_link_todo_to_pr(todoId, prNumber)\`

**After merge to dev:**
- Update todo status to \`done\`: \`mcp_update_todo_status(todoId, "done")\` (only after tested AND merged!)

**CRITICAL Git Rules:**
- 🚨 ALWAYS check branch before starting work on a feature!
- NEVER commit without testing first!
- NEVER commit to main/master directly! Always use feature branches
- NEVER commit on wrong branch (e.g., develop when working on a feature)
- ALWAYS check git status before committing
- ALWAYS use the commit message format with feature ID
- ALWAYS push after committing
- ALWAYS update todo status after committing (tested) and after merge (done)

## InTracker Integration

**ALWAYS use InTracker to track progress - this is NOT optional!**

**Todo Management:**
- Create todos: \`mcp_create_todo(elementId, title, description, featureId?, priority?)\`
- Update status: \`mcp_update_todo_status(todoId, status, expectedVersion?)\`
- Get active todos: \`mcp_get_active_todos(projectId, status?, featureId?)\`

**Feature Management:**
- Create features: \`mcp_create_feature(projectId, name, description, elementIds?)\`
- Update feature status: \`mcp_update_feature_status(featureId, status)\`
- Get feature: \`mcp_get_feature(featureId)\`

**Project Context:**
- Get resume context: \`mcp_get_resume_context(projectId)\`
- Get project context: \`mcp_get_project_context(projectId)\`
- Identify project: \`mcp_identify_project_by_path(path)\`

---

**Generated by InTracker**
**For project-specific rules, use \`mcp_load_cursor_rules(projectId)\` after project identification**`

const guideSections: GuideSection[] = [
  {
    id: 'base-rules',
    title: 'Alap Cursor Rules Betöltése',
    description: 'Egy gombnyomással töltsd be az alap InTracker workflow rules-t a Cursor-ba',
    icon: <BookOpen className="w-5 h-5" />,
    color: 'text-emerald-500',
    steps: [
      {
        title: 'InTracker Alap Workflow Rules',
        description: 'Ez az alap rules tartalmazza az InTracker használatának alapvető workflow-ját, amit minden agentnek követnie kell. Kattints a gombra, hogy egyből felvedd a Cursor-ba!',
        type: 'cursor',
        command: 'Add InTracker Workflow Rules to Cursor',
        deeplink: generateRuleDeeplink('intracker-workflow', INTracker_BASE_RULES),
        code: 'A rules tartalmazza:\n- Session start workflow (mcp_enforce_workflow)\n- Branch ellenőrzés (KÖTELEZŐ feature munkához)\n- Todo státusz workflow (new → in_progress → tested → done)\n- Git workflow (commit formátum, push, merge)\n- InTracker integráció (MCP tool-ok használata)',
        tips: [
          'Ez az alap rules minden projektnél használható',
          'Projekt-specifikus rules-t a mcp_load_cursor_rules tool tölti be',
          'A rules automatikusan mentődik a .cursor/rules/intracker-workflow.mdc fájlba',
          'A Cursor automatikusan betölti a .cursor/rules/ mappában lévő fájlokat',
          'A deeplink megnyitása után a Cursor megkérdezi, hogy hozzá szeretnéd-e adni a rules-t'
        ]
      }
    ]
  },
  {
    id: 'prompt-best-practice',
    title: 'Prompt Best Practice',
    description: 'Hasznos prompt ötletek az InTracker-rel való hatékony munkához',
    icon: <Lightbulb className="w-5 h-5" />,
    color: 'text-amber-500',
    steps: [
      {
        title: '1. Projekt Azonosítás és Setup',
        description: 'Prompt ötletek új projekt beállításához',
        type: 'cursor',
        command: 'Azonosítsd a projektet a jelenlegi munkakönyvtárból és töltsd be a resume context-et',
        deeplink: generateCursorDeeplink('Azonosítsd a projektet a jelenlegi munkakönyvtárból és töltsd be a resume context-et. Használd az mcp_identify_project_by_path és mcp_get_resume_context tool-okat.'),
        tips: [
          'Használd az mcp_identify_project_by_path tool-t a projekt azonosításához',
          'Töltsd be a resume context-et az mcp_get_resume_context tool-lal',
          'Ha nincs projekt, hozd létre az mcp_create_project tool-lal'
        ]
      },
      {
        title: '2. Új Feature Létrehozása',
        description: 'Prompt ötlet új feature létrehozásához',
        type: 'cursor',
        command: 'Hozz létre egy új feature-t a projektben. Kérdezd le a projekt elemeit és válassz ki releváns elemeket a feature-höz.',
        deeplink: generateCursorDeeplink('Hozz létre egy új feature-t a projektben. Kérdezd le a projekt elemeit az mcp_get_project_structure tool-lal és válassz ki releváns elemeket. Használd az mcp_create_feature tool-t.'),
        tips: [
          'Kérdezd le a projekt struktúráját: mcp_get_project_structure',
          'Válassz ki releváns elemeket a feature-höz',
          'Használd az mcp_create_feature tool-t a feature létrehozásához'
        ]
      },
      {
        title: '3. Todo-k Létrehozása Feature-hez',
        description: 'Prompt ötlet todo-k létrehozásához egy feature-hez',
        type: 'cursor',
        command: 'Hozz létre részletes todo-kat egy feature-hez. Minden todo legyen specifikus, mérhető és végrehajtható.',
        deeplink: generateCursorDeeplink('Hozz létre részletes todo-kat egy feature-hez. Minden todo legyen specifikus, mérhető és végrehajtható. Használd az mcp_create_todo tool-t és linkeld a feature-hez.'),
        tips: [
          'Használd az mcp_get_feature tool-t a feature részleteinek lekéréséhez',
          'Hozz létre todo-kat az mcp_create_todo tool-lal',
          'Linkeld a todo-kat a feature-hez a featureId paraméterrel',
          'Használd a team nyelvét a todo cím és leírás létrehozásánál!'
        ]
      },
      {
        title: '4. Következő Todo Elvégzése',
        description: 'Prompt ötlet a következő todo elvégzéséhez',
        type: 'cursor',
        command: 'Kérdezd le a következő todo-kat a projektből és kezdj el dolgozni az első új todo-n. ELLENŐRIZD A BRANCH-ET mielőtt elkezdesz dolgozni!',
        deeplink: generateCursorDeeplink('Kérdezd le a következő todo-kat az mcp_get_active_todos tool-lal. ELLENŐRIZD A BRANCH-ET mielőtt elkezdesz dolgozni! Ha feature-n dolgozol, válts a feature branch-re. Frissítsd a todo státuszát in_progress-re.'),
        tips: [
          'Kérdezd le az aktív todo-kat: mcp_get_active_todos',
          '🚨 MINDIG ellenőrizd a branch-et mielőtt elkezdesz dolgozni!',
          'Frissítsd a todo státuszát in_progress-re: mcp_update_todo_status',
          'Használd az expectedVersion-t az optimistic locking-hoz'
        ]
      },
      {
        title: '5. Feature Branch Létrehozása',
        description: 'Prompt ötlet feature branch létrehozásához',
        type: 'cursor',
        command: 'Hozz létre egy feature branch-et egy feature-hez és válts rá. Ellenőrizd, hogy a megfelelő branch-en vagy mielőtt elkezdesz dolgozni.',
        deeplink: generateCursorDeeplink('Hozz létre egy feature branch-et egy feature-hez az mcp_create_branch_for_feature tool-lal. Válts rá a git checkout paranccsal. Ellenőrizd a branch-et a git branch --show-current paranccsal.'),
        tips: [
          'Kérdezd le a feature-t: mcp_get_feature',
          'Hozd létre a feature branch-et: mcp_create_branch_for_feature',
          'Válts a feature branch-re: git checkout feature/{feature-name}',
          'Húzd le a legfrissebbet: git pull origin feature/{feature-name}'
        ]
      },
      {
        title: '6. Változások Commit-olása',
        description: 'Prompt ötlet változások commit-olásához',
        type: 'cursor',
        command: 'Commit-old a változásokat a megfelelő formátumban. Ellenőrizd a git státuszt, add hozzá a változásokat, és commit-old a feature ID-vel.',
        deeplink: generateCursorDeeplink('Commit-old a változásokat a megfelelő formátumban. Ellenőrizd a git státuszt, add hozzá a változásokat (git add -A), és commit-old a következő formátumban: {type}({scope}): {description} [feature:{featureId}]. Frissítsd a todo státuszát tested-re.'),
        tips: [
          'Ellenőrizd a git státuszt: git status',
          'Nézd át a változásokat: git diff',
          'Add hozzá a változásokat: git add -A',
          'Commit-old a megfelelő formátumban: {type}({scope}): {description} [feature:{featureId}]',
          'Push-old a változásokat: git push origin {branch-name}',
          'Frissítsd a todo státuszát tested-re: mcp_update_todo_status'
        ]
      },
      {
        title: '7. Projekt Struktúra Elemzése',
        description: 'Prompt ötlet projekt struktúra elemzéséhez',
        type: 'cursor',
        command: 'Elemezd a projekt fájlstruktúráját és hozz létre projekt elemeket automatikusan. Használd az mcp_parse_file_structure tool-t.',
        deeplink: generateCursorDeeplink('Elemezd a projekt fájlstruktúráját és hozz létre projekt elemeket automatikusan. Használd az mcp_parse_file_structure tool-t a projekt ID-val és a projekt path-tal.'),
        tips: [
          'Használd az mcp_parse_file_structure tool-t',
          'Csak akkor működik, ha nincsenek még elemek a projektben',
          'Automatikusan létrehozza a hierarchikus projekt elemeket',
          'A maxDepth paraméterrel szabályozhatod a mélységet (alapértelmezett: 3)'
        ]
      },
      {
        title: '8. GitHub Issue-k Importálása',
        description: 'Prompt ötlet GitHub issue-k importálásához',
        type: 'cursor',
        command: 'Importáld a GitHub issue-kat todo-kként a projektbe. Először kapcsold össze a GitHub repository-t, majd importáld az issue-kat.',
        deeplink: generateCursorDeeplink('Importáld a GitHub issue-kat todo-kként a projektbe. Először kapcsold össze a GitHub repository-t az mcp_connect_github_repo tool-lal, majd importáld az issue-kat az mcp_import_github_issues tool-lal.'),
        tips: [
          'Kapcsold össze a GitHub repository-t: mcp_connect_github_repo',
          'Importáld az issue-kat: mcp_import_github_issues',
          'Az issue-k automatikusan todo-kká válnak',
          'A createElements=true automatikusan létrehoz elemeket, ha szükséges'
        ]
      },
      {
        title: '9. Feature Progress Ellenőrzése',
        description: 'Prompt ötlet feature progress ellenőrzéséhez',
        type: 'cursor',
        command: 'Kérdezd le egy feature részletes információit, beleértve a todo-kat, az elemeket és a progress százalékot.',
        deeplink: generateCursorDeeplink('Kérdezd le egy feature részletes információit az mcp_get_feature tool-lal. Nézd meg a todo-kat, az elemeket és a progress százalékot.'),
        tips: [
          'Használd az mcp_get_feature tool-t',
          'A feature progress automatikusan számolódik a todo-k alapján',
          'Kérdezd le a feature todo-kat: mcp_get_feature_todos',
          'Kérdezd le a feature elemeket: mcp_get_feature_elements'
        ]
      },
      {
        title: '10. Session Összefoglaló',
        description: 'Prompt ötlet session végén összefoglaló készítéséhez',
        type: 'cursor',
        command: 'Készíts egy összefoglalót a session-ről. Listázd a befejezett todo-kat, feature-öket és jegyezd fel a következő lépéseket.',
        deeplink: generateCursorDeeplink('Készíts egy összefoglalót a session-ről. Listázd a befejezett todo-kat, feature-öket és jegyezd fel a következő lépéseket. Használd az mcp_end_session tool-t a session lezárásához.'),
        tips: [
          'Kérdezd le a befejezett todo-kat és feature-öket',
          'Készíts egy részletes összefoglalót',
          'Használd az mcp_end_session tool-t a session lezárásához',
          'A következő session-ben a resume context tartalmazza ezt az információt'
        ]
      }
    ]
  },
  {
    id: 'branch-check',
    title: 'Branch Ellenőrzés',
    description: 'KRITIKUS: Mindig ellenőrizd a branch-et feature munkához!',
    icon: <GitBranch className="w-5 h-5" />,
    color: 'text-orange-500',
    steps: [
      {
        title: '1. Ellenőrizd az aktuális branch-t',
        description: 'Terminal command a branch ellenőrzéséhez',
        type: 'terminal',
        command: 'git branch --show-current',
        tips: [
          'MINDIG ellenőrizd mielőtt elkezdesz dolgozni!',
          'Ha feature-n dolgozol, KÖTELEZŐ a feature branch használata'
        ]
      },
      {
        title: '2. Feature branch lekérése',
        description: 'Kérdezd le a feature branch-eket',
        type: 'cursor',
        command: 'mcp_get_feature_branches(featureId="your-feature-id")',
        deeplink: generateCursorDeeplink('Use the mcp_get_feature_branches tool'),
        warning: 'Ha nincs feature branch, hozd létre: mcp_create_branch_for_feature'
      },
      {
        title: '3. Válts feature branch-re',
        description: 'Ha van feature branch, válts rá',
        type: 'terminal',
        command: 'git checkout feature/feature-name\ngit pull origin feature/feature-name',
        tips: [
          'Ha NINCS feature branch, hozd létre: mcp_create_branch_for_feature',
          'Ha NEM feature-n dolgozol, használd a develop branch-et'
        ]
      }
    ]
  },
  {
    id: 'todo-workflow',
    title: 'Todo Workflow',
    description: 'Todo státusz frissítés workflow',
    icon: <CheckCircle2 className="w-5 h-5" />,
    color: 'text-green-500',
    steps: [
      {
        title: '1. Todo munkakezdés',
        description: 'Amikor elkezdesz dolgozni egy todo-n',
        type: 'cursor',
        command: 'mcp_update_todo_status(todoId="todo-uuid", status="in_progress", expectedVersion=1)',
        deeplink: generateCursorDeeplink('Use the mcp_update_todo_status tool with status=in_progress'),
        tips: [
          'Fontos: Az expectedVersion az előző olvasásból jön (optimistic locking)',
          'Először olvasd be a todo-t: mcp_get_active_todos'
        ]
      },
      {
        title: '2. Tesztelés után',
        description: 'Amikor tesztelted a változtatásokat',
        type: 'cursor',
        command: 'mcp_update_todo_status(todoId="todo-uuid", status="tested", expectedVersion=2)',
        deeplink: generateCursorDeeplink('Use the mcp_update_todo_status tool with status=tested'),
        warning: 'Csak akkor frissítsd tested-re, ha tényleg tesztelted!'
      },
      {
        title: '3. Merge után',
        description: 'Amikor a feature branch merge-olódott dev-be',
        type: 'cursor',
        command: 'mcp_update_todo_status(todoId="todo-uuid", status="done", expectedVersion=3)',
        deeplink: generateCursorDeeplink('Use the mcp_update_todo_status tool with status=done'),
        warning: 'Csak akkor frissítsd done-ra, ha tested ÉS merged!'
      }
    ]
  },
  {
    id: 'git-workflow',
    title: 'Git Workflow',
    description: 'Kötelező git workflow lépések',
    icon: <Terminal className="w-5 h-5" />,
    color: 'text-purple-500',
    steps: [
      {
        title: '1. Commit előtt - Status ellenőrzés',
        description: 'MINDIG ellenőrizd a git státuszt commit előtt',
        type: 'terminal',
        command: 'git status\ngit diff',
        tips: [
          'Ellenőrizd, hogy a megfelelő fájlok vannak módosítva',
          'Nézd át a diff-et, hogy nincs-e véletlen változtatás'
        ]
      },
      {
        title: '2. Staging',
        description: 'Add hozzá az összes változtatást',
        type: 'terminal',
        command: 'git add -A\ngit status',
        tips: [
          'Ellenőrizd a staged fájlokat',
          'Győződj meg róla, hogy csak a szükséges fájlok vannak staged'
        ]
      },
      {
        title: '3. Commit (KÖTELEZŐ formátum!)',
        description: 'Commit message formátum: type(scope): description [feature:featureId]',
        type: 'terminal',
        command: 'git commit -m "feat(scope): Description [feature:feature-uuid]\n\n- [x] Todo item 1\n- [x] Todo item 2"',
        tips: [
          'Típusok: feat, fix, refactor, docs, test, chore',
          'MINDIG tartalmazd a feature ID-t!',
          'Listázd a befejezett todo-kat a commit message-ben'
        ],
        warning: 'SOHA ne commit-olj rossz formátummal!'
      },
      {
        title: '4. Push',
        description: 'Push-olás a remote-ra',
        type: 'terminal',
        command: 'git push origin feature/feature-name',
        tips: [
          'MINDIG push-olj commit után',
          'Ellenőrizd, hogy a megfelelő branch-re push-olsz'
        ]
      }
    ]
  },
  {
    id: 'quick-actions',
    title: 'Quick Actions',
    description: 'Gyorsan használható MCP tool-ok',
    icon: <Lightbulb className="w-5 h-5" />,
    color: 'text-yellow-500',
    steps: [
      {
        title: 'Resume Context Lekérése',
        description: 'Aktuális projekt állapot lekérése',
        type: 'cursor',
        command: 'mcp_get_resume_context(projectId="project-uuid")',
        deeplink: generateCursorDeeplink('Use the mcp_get_resume_context tool'),
        tips: [
          'Tartalmazza: Last session, Next todos, Active elements, Blockers, Constraints'
        ]
      },
      {
        title: 'Aktív Todo-k Lekérése',
        description: 'Következő todo-k lekérése',
        type: 'cursor',
        command: 'mcp_get_active_todos(projectId="project-uuid", status="new")',
        deeplink: generateCursorDeeplink('Use the mcp_get_active_todos tool'),
        tips: [
          'Szűrhető státusz szerint: new, in_progress, done',
          'Szűrhető feature szerint is'
        ]
      },
      {
        title: 'Feature Lekérése',
        description: 'Feature részletes információi',
        type: 'cursor',
        command: 'mcp_get_feature(featureId="feature-uuid")',
        deeplink: generateCursorDeeplink('Use the mcp_get_feature tool'),
        tips: [
          'Tartalmazza: Feature info, Todo-k, Elements, Progress'
        ]
      },
      {
        title: 'Projekt Kontextus Lekérése',
        description: 'Teljes projekt információ',
        type: 'cursor',
        command: 'mcp_get_project_context(projectId="project-uuid")',
        deeplink: generateCursorDeeplink('Use the mcp_get_project_context tool'),
        tips: [
          'Nagy projekteknél használd a featuresLimit és todosLimit paramétereket',
          'summaryOnly=true csak összefoglalót ad vissza'
        ]
      }
    ]
  },
  {
    id: 'session-start',
    title: 'Session Kezdés',
    description: 'Minden session elején KÖTELEZŐ ezt a lépést követni',
    icon: <Rocket className="w-5 h-5" />,
    color: 'text-blue-500',
    steps: [
      {
        title: '1. Enforce Workflow (KÖTELEZŐ!)',
        description: 'Automatikusan azonosítja a projektet, betölti a resume context-et és cursor rules-t',
        type: 'cursor',
        command: 'mcp_enforce_workflow()',
        deeplink: generateCursorDeeplink('Use the mcp_enforce_workflow tool to start the session'),
        tips: [
          'Ez a tool automatikusan azonosítja a projektet',
          'Betölti a resume context-et (Last/Now/Blockers)',
          'Betölti a cursor rules-t',
          'Visszaadja a workflow checklist-et'
        ]
      },
      {
        title: '2. Cursor Rules Betöltése (Opció)',
        description: 'Ha manuálisan szeretnéd betölteni a cursor rules-t, amely tartalmazza az alap workflow-t és best practice-eket',
        type: 'cursor',
        command: 'mcp_load_cursor_rules(projectId="your-project-id", projectPath=".")',
        deeplink: generateCursorDeeplink('Use the mcp_load_cursor_rules tool to load project-specific cursor rules'),
        tips: [
          'A cursor rules tartalmazza az alap workflow-t: projekt azonosítás, resume context, branch ellenőrzés, git workflow',
          'Automatikusan létrehozza a `.cursor/rules/intracker-project-rules.mdc` fájlt a projektben',
          'A rules tartalmazza a projekt-specifikus instrukciókat és best practice-eket',
          'Az `mcp_enforce_workflow` automatikusan betölti a cursor rules-t is'
        ],
        code: '// A cursor rules tartalmazza:\n// - Core workflow (projekt azonosítás, resume context)\n// - Branch ellenőrzés és git workflow\n// - Todo és feature státusz workflow\n// - Projekt-specifikus instrukciók\n// - Best practices az InTracker használatához'
      }
    ]
  }
]

export function CursorGuide() {
  const [copiedCommands, setCopiedCommands] = useState<Set<string>>(new Set())
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['base-rules', 'session-start']))

  const handleCopy = (text: string, commandId: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCommands(prev => new Set(prev).add(commandId))
    setTimeout(() => {
      setCopiedCommands(prev => {
        const newSet = new Set(prev)
        newSet.delete(commandId)
        return newSet
      })
    }, 2000)
  }

  const handleDeeplink = (deeplink: string) => {
    window.location.href = deeplink
  }

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <PageHeader
        title={
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-primary" />
            <span>Cursor + InTracker Guide</span>
          </div>
        }
        description="Interaktív útmutató a Cursor és InTracker hatékony használatához. Minden lépéshez copy-paste ready példákat találsz."
      />

      <div className="space-y-4">
        {guideSections.map((section) => {
          const isExpanded = expandedSections.has(section.id)
          
          return (
            <Card key={section.id} className="overflow-hidden">
              <CardHeader 
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => toggleSection(section.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-lg bg-muted", section.color)}>
                      {section.icon}
                    </div>
                    <div>
                      <CardTitle className="text-xl">{section.title}</CardTitle>
                      <CardDescription className="mt-1">{section.description}</CardDescription>
                    </div>
                  </div>
                  <ChevronRight 
                    className={cn(
                      "w-5 h-5 text-muted-foreground transition-transform",
                      isExpanded && "transform rotate-90"
                    )}
                  />
                </div>
              </CardHeader>
              
              {isExpanded && (
                <CardContent className="space-y-4">
                  {section.steps.map((step, stepIndex) => {
                    const commandId = `${section.id}-${stepIndex}`
                    const isCopied = copiedCommands.has(commandId)
                    const displayCommand = step.command || step.code || ''
                    
                    return (
                      <div key={stepIndex} className="space-y-3 p-4 rounded-lg border border-border/50 bg-muted/30">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h4 className="font-semibold text-base">{step.title}</h4>
                              {step.type === 'cursor' && (
                                <Badge variant="outline" className="text-xs">MCP Tool</Badge>
                              )}
                              {step.type === 'terminal' && (
                                <Badge variant="outline" className="text-xs">Terminal</Badge>
                              )}
                              {step.type === 'info' && (
                                <Badge variant="outline" className="text-xs">Info</Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-3">{step.description}</p>
                            
                            {displayCommand && (
                              <div className="relative group">
                                <div className="flex items-center gap-2 mb-2">
                                  <code className="flex-1 px-3 py-2 bg-background border border-border rounded-md text-sm font-mono overflow-x-auto">
                                    {displayCommand}
                                  </code>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleCopy(displayCommand, commandId)}
                                    className="shrink-0"
                                  >
                                    {isCopied ? (
                                      <Check className="w-4 h-4 text-green-500" />
                                    ) : (
                                      <Copy className="w-4 h-4" />
                                    )}
                                  </Button>
                                  {step.deeplink && (
                                    <Button
                                      variant="default"
                                      size="sm"
                                      onClick={() => handleDeeplink(step.deeplink!)}
                                      className="shrink-0"
                                    >
                                      <Play className="w-4 h-4 mr-1" />
                                      Run in Cursor
                                    </Button>
                                  )}
                                </div>
                              </div>
                            )}
                            
                            {step.tips && step.tips.length > 0 && (
                              <div className="mt-3 space-y-1">
                                {step.tips.map((tip, tipIndex) => (
                                  <div key={tipIndex} className="flex items-start gap-2 text-sm text-muted-foreground">
                                    <Lightbulb className="w-4 h-4 mt-0.5 text-yellow-500 shrink-0" />
                                    <span>{tip}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {step.warning && (
                              <div className="mt-3 flex items-start gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-md">
                                <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
                                <span className="text-sm text-orange-700 dark:text-orange-400">{step.warning}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>

      <Card className="mt-8 border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-primary" />
            Fontos Emlékeztetők
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              <span><strong>MINDIG</strong> használd az <code className="px-1 py-0.5 bg-background rounded text-xs">mcp_enforce_workflow</code> tool-t session elején!</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              <span><strong>MINDIG</strong> ellenőrizd a branch-et feature munkához!</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              <span><strong>MINDIG</strong> használd az <code className="px-1 py-0.5 bg-background rounded text-xs">expectedVersion</code>-t todo státusz frissítésnél!</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              <span><strong>MINDIG</strong> kövesd a git workflow sorrendet!</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              <span><strong>MINDIG</strong> teszteld a változtatásokat commit előtt!</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
