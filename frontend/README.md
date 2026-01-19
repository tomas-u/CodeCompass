# CodeCompass Frontend

Next.js 14+ frontend for CodeCompass code analysis platform.

## Features

- **Project Dashboard**: View and manage code analysis projects
- **Real-time Status**: Live polling of analysis progress
- **AI Chat Panel**: RAG-powered Q&A with streaming responses
- **Mermaid Diagrams**: Interactive architecture visualizations
- **File Browser**: Explore analyzed codebase structure
- **Keyboard Shortcuts**: Ctrl+K to toggle chat, Escape to minimize

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running on http://localhost:8000

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home/landing page
│   │   └── projects/           # Project pages
│   │       ├── page.tsx        # Project list
│   │       ├── new/page.tsx    # Create project
│   │       └── [id]/page.tsx   # Project detail
│   ├── components/
│   │   ├── layout/             # Layout components
│   │   │   ├── ChatPanel.tsx   # AI chat with streaming
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── project/            # Project components
│   │   │   ├── OverviewTab.tsx
│   │   │   ├── DiagramsTab.tsx
│   │   │   └── FilesTab.tsx
│   │   └── ui/                 # shadcn/ui components
│   ├── hooks/
│   │   └── useProjectStatus.ts # Real-time status polling
│   ├── lib/
│   │   ├── api.ts              # API client with SSE support
│   │   ├── api-config.ts       # API configuration
│   │   └── store.ts            # Zustand state management
│   └── types/
│       └── api.ts              # TypeScript API types
├── tests/
│   └── e2e/                    # Playwright E2E tests
│       ├── chat.spec.ts        # Chat panel tests
│       ├── project-creation.spec.ts
│       └── analyze-workflow.spec.ts
├── playwright.config.ts        # Playwright configuration
├── tailwind.config.js
└── next.config.js
```

## Testing

### E2E Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run in debug mode
npm run test:e2e:debug

# View test report
npm run test:e2e:report
```

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| `chat.spec.ts` | Chat panel, keyboard shortcuts, streaming |
| `project-creation.spec.ts` | Project creation flow |
| `analyze-workflow.spec.ts` | Analysis trigger and status |

## Key Components

### ChatPanel

AI-powered chat with streaming responses:
- Toggle with Ctrl+K keyboard shortcut
- Real-time token streaming via SSE
- Source citations with file links
- Message history with clear functionality

### useProjectStatus Hook

Real-time status polling:
- Polls every 2 seconds during analysis
- Stops at terminal states (ready, failed)
- Cleanup on unmount to prevent memory leaks

### API Client

Full-featured API client:
- RESTful endpoints for CRUD operations
- SSE streaming for chat responses
- Error handling with typed responses

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand
- **Types**: TypeScript
- **Testing**: Playwright
- **Diagrams**: Mermaid.js

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Playwright](https://playwright.dev)
