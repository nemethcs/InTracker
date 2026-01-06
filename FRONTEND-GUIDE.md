# Frontend Architecture & Implementation Guide

## Technology Stack

### Core Framework
- **React 18+** with TypeScript
- **Vite** - Build tool and dev server
- **React Router v6** - Client-side routing

### State Management
- **Zustand** - Lightweight state management
- **TanStack Query** (optional) - Server state management

### UI & Styling
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality component library
- **Lucide React** - Icon library

### API & Data
- **Axios** - HTTP client
- **@microsoft/signalr** - Real-time WebSocket communication

### Development Tools
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript** - Type safety

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # Base UI components (shadcn/ui)
│   │   ├── projects/        # Project-related components
│   │   ├── features/         # Feature components
│   │   ├── todos/           # Todo components
│   │   ├── elements/         # Element tree components
│   │   ├── documents/        # Document components
│   │   ├── sessions/         # Session components
│   │   └── layout/          # Layout components
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx
│   │   ├── ProjectDetail.tsx
│   │   ├── Login.tsx
│   │   └── Register.tsx
│   ├── stores/              # Zustand stores
│   │   ├── authStore.ts
│   │   ├── projectStore.ts
│   │   ├── featureStore.ts
│   │   ├── todoStore.ts
│   │   └── sessionStore.ts
│   ├── services/            # API services
│   │   ├── api.ts           # Axios instance
│   │   ├── authService.ts
│   │   ├── projectService.ts
│   │   ├── featureService.ts
│   │   └── signalrService.ts
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useProject.ts
│   │   ├── useFeatures.ts
│   │   └── useTodos.ts
│   ├── types/               # TypeScript types
│   │   ├── project.ts
│   │   ├── feature.ts
│   │   └── todo.ts
│   ├── utils/               # Utility functions
│   ├── App.tsx              # Main app component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── .env.example
```

## Key Features

### 1. Authentication
- JWT token-based authentication
- Token refresh mechanism
- Protected routes
- Auto-logout on token expiry

### 2. Project Management
- Project list with filtering
- Quick project switching
- Project creation and editing
- Project statistics dashboard

### 3. Feature & Todo Management
- Hierarchical element tree view
- Feature progress tracking
- Todo status management
- Drag-and-drop support (future)

### 4. Real-time Collaboration
- Live updates via SignalR
- Active user indicators
- Conflict warnings
- Real-time notifications

### 5. Resume Context
- Last session summary
- Active todos display
- Next steps suggestions
- Blockers and constraints view

## Implementation Phases

### Phase 1: Setup & Foundation
- Project initialization
- Dependencies installation
- Basic routing
- Authentication flow

### Phase 2: Core Components
- UI component library setup
- Layout system
- Basic pages (Dashboard, Project Detail)

### Phase 3: State Management
- Zustand stores implementation
- API service layer
- Custom hooks

### Phase 4: Real-time Features
- SignalR integration
- Live updates
- Collaboration features

## API Integration

All API calls go through centralized service layer:
- Base URL configuration
- Request/response interceptors
- Error handling
- Token management
- Loading states

## State Management Strategy

- **Zustand stores** for client-side state
- **React Query** (optional) for server state caching
- **SignalR** for real-time updates
- Local state for UI-only concerns

## Component Architecture

### Layout Components
- `MainLayout` - Main app layout with header/sidebar
- `Header` - Top navigation bar
- `Sidebar` - Project navigation sidebar
- `ProjectSwitcher` - Quick project switching dropdown

### Project Components
- `ProjectList` - List of user projects
- `ProjectCard` - Project card component
- `ProjectView` - Full project detail view
- `ResumeContext` - Resume context display

### Feature Components
- `FeatureList` - List of features
- `FeatureCard` - Feature card with progress
- `FeatureView` - Feature detail with todos

### Todo Components
- `TodoList` - List of todos
- `TodoCard` - Todo card component
- `TodoEditor` - Todo create/edit form

### Element Components
- `ElementTree` - Hierarchical element tree
- `ElementCard` - Element card component
- `ElementEditor` - Element create/edit form

## Routing Structure

```
/                    → Dashboard
/login               → Login page
/register            → Register page
/projects            → Project list
/projects/:id        → Project detail
/projects/:id/features → Feature list
/projects/:id/todos  → Todo list
```

## Environment Variables

```env
VITE_API_BASE_URL=http://localhost:3000
VITE_SIGNALR_URL=http://localhost:3000/hub
VITE_APP_NAME=InTracker
```

## Development Workflow

1. Start dev server: `npm run dev`
2. Build for production: `npm run build`
3. Preview production build: `npm run preview`
4. Lint: `npm run lint`
5. Format: `npm run format`

## Testing Strategy

- Unit tests: Vitest
- Component tests: React Testing Library
- E2E tests: Playwright (future)

## Deployment

- **Development:** Vite dev server
- **Production:** Static build (Azure Static Web Apps or similar)
