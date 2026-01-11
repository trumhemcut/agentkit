# Settings Page Implementation Plan

## Overview
Implementation plan for adding a Settings page where users can configure agent parameters (provider, LLM, agent name, system prompts, etc.). This plan focuses on UI/UX implementation first.

**Requirement Reference**: `.docs/0-requirements/033-settings-page.md`

---

## Architecture Overview

### Route Structure
- New route: `/settings` (using Next.js App Router)
- Settings accessible from sidebar bottom section
- Mobile-friendly responsive design

### Component Hierarchy
```
app/settings/page.tsx (Settings Page Route)
└── components/Settings/
    ├── SettingsLayout.tsx (Main settings container)
    ├── ProviderSettings.tsx (Provider configuration)
    ├── ModelSettings.tsx (Model configuration)
    ├── AgentSettings.tsx (Agent name, type settings)
    ├── SystemPromptSettings.tsx (System prompt editor)
    └── AdvancedSettings.tsx (Other options)
```

---

## Frontend Tasks

### Task 1: Add Settings Navigation to Sidebar
**Component**: `frontend/components/Sidebar.tsx`
**Changes**:
- Add Settings button at the bottom of sidebar (below thread list)
- Use `Settings` icon from lucide-react
- Desktop: Show with icon + "Settings" text
- Mobile: Show in mobile drawer
- Navigate to `/settings` on click

**Acceptance Criteria**:
- Settings button visible at bottom of sidebar
- Button styled consistently with existing UI
- Mobile drawer includes Settings option
- Clicking navigates to `/settings` route

---

### Task 2: Create Settings Page Route
**New File**: `frontend/app/settings/page.tsx`
**Purpose**: Main Settings page route component
**Features**:
- Page title "Settings"
- Back navigation to chat
- Responsive layout container
- Renders SettingsLayout component

**Acceptance Criteria**:
- Route `/settings` accessible
- Page has proper metadata/title
- Mobile-responsive layout
- Back navigation works

---

### Task 3: Create Settings Layout Component
**New File**: `frontend/components/Settings/SettingsLayout.tsx`
**Purpose**: Main container for settings sections
**Features**:
- Responsive grid/flex layout
- Section cards using Shadcn UI Card component
- Mobile-friendly spacing and sizing
- Sections for:
  - Provider Settings
  - Model Settings
  - Agent Settings
  - System Prompt Settings
  - Advanced Settings

**Design Pattern**:
- Use Card components with sections
- Stack sections vertically on mobile
- Side-by-side or grid on desktop (if applicable)
- Clear section headers and descriptions

**Acceptance Criteria**:
- Clean, organized layout
- Works on mobile (320px+) and desktop
- Uses existing Shadcn UI components
- Proper spacing and visual hierarchy

---

### Task 4: Implement Provider Settings Section
**New File**: `frontend/components/Settings/ProviderSettings.tsx`
**Purpose**: Configure AI provider
**Features**:
- Display available providers (from modelStore)
- Radio group or select dropdown for provider selection
- Show provider status (available/unavailable)
- Visual feedback for selected provider

**Integration**:
- Use existing `useModelStore` hook
- Update provider via `setSelectedProvider`

**Acceptance Criteria**:
- Lists available providers
- Can select provider
- Shows current selection
- Updates modelStore state

---

### Task 5: Implement Model Settings Section
**New File**: `frontend/components/Settings/ModelSettings.tsx`
**Purpose**: Configure LLM model
**Features**:
- Display available models for selected provider
- Model selection with name, size info
- Show model availability status
- Visual feedback for selected model

**Integration**:
- Use existing `useModelStore` hook
- Filter models by selected provider
- Update model via `setSelectedModel`

**Acceptance Criteria**:
- Lists models for selected provider
- Can select model
- Shows model details (name, size)
- Updates modelStore state

---

### Task 6: Implement Agent Settings Section
**New File**: `frontend/components/Settings/AgentSettings.tsx`
**Purpose**: Configure agent properties
**Features**:
- Display available agents (from agentStore)
- Agent selection dropdown
- Agent description display
- Future: Agent name customization field

**Integration**:
- Use existing `useAgentStore` hook
- Update agent via `setSelectedAgent`

**Acceptance Criteria**:
- Lists available agents
- Can select agent
- Shows agent description
- Updates agentStore state

---

### Task 7: Implement System Prompt Settings Section
**New File**: `frontend/components/Settings/SystemPromptSettings.tsx`
**Purpose**: Edit system prompts for agents
**Features**:
- Textarea for system prompt editing
- Character count display
- Preview of current prompt
- Save/Reset functionality

**Design**:
- Use Shadcn UI Textarea component
- Clear labels and help text
- Mobile-friendly textarea size

**Acceptance Criteria**:
- Can edit system prompt
- Character count visible
- Save/Reset buttons work
- Mobile-friendly textarea

---

### Task 8: Add Save/Cancel Actions
**Component**: `frontend/components/Settings/SettingsLayout.tsx`
**Features**:
- Save button (primary action)
- Cancel button (secondary action)
- Sticky footer on mobile (optional)
- Success toast notification on save
- Confirmation dialog for unsaved changes

**Acceptance Criteria**:
- Save/Cancel buttons visible
- Save persists settings
- Cancel discards changes
- User feedback on save

---

### Task 9: Settings Persistence
**Approach**: Use existing localStorage patterns (similar to modelStore)
**Implementation**:
- Settings auto-save on change (or via Save button)
- Load settings from localStorage on mount
- Optional: Backend API integration for persistence

**Acceptance Criteria**:
- Settings persist across sessions
- Settings load on page mount
- No data loss on refresh

---

### Task 10: Mobile Responsive Testing
**Testing**:
- Test on mobile viewport (320px - 768px)
- Test sidebar Settings navigation on mobile
- Test Settings page layout on mobile
- Test form interactions on mobile
- Test navigation back to chat

**Acceptance Criteria**:
- All components responsive
- No horizontal scroll
- Touch-friendly tap targets
- Smooth navigation

---

## Integration Points

### Existing Stores
- `modelStore`: Provider and model selection
- `agentStore`: Agent selection
- Future: `settingsStore` for additional settings

### Routing
- Next.js App Router: `/settings` route
- Navigation from Sidebar component

### UI Components
- Shadcn UI: Card, Button, Label, Input, Textarea, Select, RadioGroup
- Lucide icons: Settings, ChevronLeft, Save, X

---

## Implementation Order

1. **Task 1**: Add Settings navigation to Sidebar (immediate visual feedback)
2. **Task 2**: Create Settings page route (navigation destination)
3. **Task 3**: Create Settings layout structure (foundation)
4. **Tasks 4-7**: Implement settings sections (core functionality)
5. **Task 8**: Add Save/Cancel actions (user feedback)
6. **Task 9**: Settings persistence (data persistence)
7. **Task 10**: Mobile testing and refinement (QA)

---

## Design References

### Mobile-First Principles
- Stack sections vertically
- Full-width cards with padding
- Touch-friendly buttons (min 44px height)
- Clear section separation
- Readable font sizes (16px+ for inputs)

### Desktop Enhancements
- Wider content container (max-width)
- Optional multi-column layout for some sections
- Hover states for interactive elements

---

## Success Metrics
- Settings page accessible from sidebar
- All settings sections functional
- Mobile-responsive design (tested on multiple screen sizes)
- Settings persist across sessions
- Clear, intuitive UI/UX

---

## Future Enhancements (Out of Scope)
- Backend API for settings persistence
- User authentication and cloud sync
- Advanced agent configuration (custom tools, etc.)
- Import/Export settings
- Settings presets/templates
- Dark mode toggle (if not already supported)

---

## Notes
- Focus on UI/UX first, backend integration can come later
- Use existing component patterns from the codebase
- Maintain consistency with current design system
- Keep mobile experience smooth and responsive
