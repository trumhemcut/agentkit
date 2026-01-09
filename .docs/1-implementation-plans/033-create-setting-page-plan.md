# Implementation Plan: Settings Page

**Status**: Ready for Implementation  
**Requirement**: [033-create-setting-page.md](../.docs/0-requirements/033-create-setting-page.md)  
**Type**: Frontend-First Feature

---

## Overview

Create a Settings page for admin users to configure agents. This is a **frontend-first feature** - build the UI/UX first to validate the design, then implement backend functionality in a future iteration.

**Key Requirements:**
- Add "Settings" menu item at the bottom of the left navigation menu
- Create Settings page UI with agent configuration options
- Focus on UI/UX polish before backend integration
- Design for future backend integration

---

## 1. Frontend Tasks (NextJS + Shadcn UI)

**Owner**: Frontend Agent - See [frontend.agent.md](../.github/agents/frontend.agent.md)

### Task 1.1: Add Settings Navigation Item
**File**: `frontend/components/sidebar.tsx` (or equivalent navigation component)

- Add "Settings" menu item at the bottom of the left sidebar/menu
- Use Shadcn UI icon for settings (e.g., `Settings` icon from lucide-react)
- Add click handler to navigate to `/settings` route
- Ensure visual distinction from other menu items (e.g., separator line above it)

**Acceptance Criteria:**
- Settings menu item appears at bottom of left navigation
- Clicking navigates to settings page
- Icon and label are visually clear

### Task 1.2: Create Settings Page Route
**Files**: 
- `frontend/app/settings/page.tsx` (main settings page)
- `frontend/app/settings/layout.tsx` (optional layout wrapper)

- Create new route at `/settings`
- Implement page layout with proper title and breadcrumb
- Add responsive design for mobile/tablet/desktop

**Acceptance Criteria:**
- Route accessible via `/settings`
- Page renders with proper layout
- Responsive design works across devices

### Task 1.3: Design Settings Page UI Components
**Files**:
- `frontend/components/settings/agent-settings-list.tsx`
- `frontend/components/settings/agent-settings-card.tsx`
- `frontend/components/settings/agent-settings-form.tsx`

**Components to Create:**

#### `AgentSettingsList`
- Display list of agents with configuration options
- Use Shadcn UI Card components for each agent
- Show agent name, description, and status
- Add expand/collapse functionality for each agent

#### `AgentSettingsCard`
- Card component for individual agent settings
- Display agent metadata (name, type, status)
- Show configuration options based on agent type
- Use Shadcn UI Form components

#### `AgentSettingsForm`
- Form component for editing agent configuration
- Fields might include:
  - Agent name
  - Description
  - Enabled/disabled toggle
  - Model selection (LLM provider)
  - Temperature/parameters
  - Tools enabled/disabled
  - Custom prompts or instructions
- Use Shadcn UI Form, Input, Textarea, Switch, Select components
- Add validation (frontend-only for now)
- Save button (mock functionality for now)

**Acceptance Criteria:**
- Agent list displays all available agents
- Each agent card shows relevant configuration options
- Form is user-friendly and follows Shadcn UI patterns
- Mock data used for initial development

### Task 1.4: Create Mock Data Service
**File**: `frontend/services/settings-mock.ts`

- Create mock data for agent configurations
- Include various agent types (chat, canvas, insurance, etc.)
- Define TypeScript interfaces for settings data structure
- Simulate API responses for testing UI

**Mock Data Structure:**
```typescript
interface AgentSettings {
  id: string;
  name: string;
  type: string;
  description: string;
  enabled: boolean;
  configuration: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    tools?: string[];
    customInstructions?: string;
  };
}
```

**Acceptance Criteria:**
- Mock service returns realistic agent settings data
- Data structure aligns with future backend API design
- Easy to swap with real API later

### Task 1.5: Add State Management
**Files**:
- `frontend/stores/settings-store.ts` (if using Zustand/similar)
- Or use React hooks in components

- Manage settings page state (selected agent, form values, etc.)
- Handle form changes and validation
- Prepare for future API integration

**Acceptance Criteria:**
- Settings state properly managed
- Form changes reflected in UI
- State structure supports future backend integration

### Task 1.6: Implement UI/UX Polish
**Files**: Various component files

- Add loading states (skeleton components)
- Add empty states (no agents configured)
- Add success/error toast notifications (mock for now)
- Ensure proper spacing, typography, and colors (Shadcn UI theme)
- Add hover states and transitions
- Test keyboard navigation and accessibility

**Acceptance Criteria:**
- UI feels polished and professional
- Loading states provide good UX
- Accessible via keyboard
- Follows Shadcn UI design patterns

---

## 2. Backend Tasks (Future Iteration)

**Owner**: Backend Agent - See [backend.agent.md](../.github/agents/backend.agent.md)

**Note**: Backend implementation is deferred to a future iteration after UI/UX is validated.

### Future Task 2.1: Create Settings Database Schema
- Define agent_settings table structure
- Add migration for settings storage
- Link settings to agents and users

### Future Task 2.2: Create Settings API Endpoints
- `GET /api/settings/agents` - List agent settings
- `GET /api/settings/agents/{agent_id}` - Get specific agent settings
- `PUT /api/settings/agents/{agent_id}` - Update agent settings
- Add authentication/authorization (admin only)

### Future Task 2.3: Implement Settings Service
- Create `settings_service.py`
- Implement CRUD operations for agent settings
- Add validation logic
- Integrate with agent registry

### Future Task 2.4: Update Agent Initialization
- Modify agents to load settings from database
- Apply settings to agent configuration
- Handle settings updates dynamically

---

## 3. Integration Points (Future)

**When backend is ready:**

### Frontend Integration Changes
**File**: `frontend/services/settings-api.ts`

- Replace mock service with real API client
- Update TypeScript interfaces to match backend models
- Add error handling for API calls
- Implement optimistic updates

### Testing Integration
- Test full flow: UI → API → Database → Agent
- Verify settings are applied to agents correctly
- Test edge cases (invalid settings, concurrent updates)

---

## 4. TypeScript Types

**File**: `frontend/types/settings.ts`

```typescript
export interface AgentSettings {
  id: string;
  name: string;
  type: AgentType;
  description: string;
  enabled: boolean;
  configuration: AgentConfiguration;
  createdAt: string;
  updatedAt: string;
}

export interface AgentConfiguration {
  model?: string;
  provider?: 'ollama' | 'openai' | 'azure' | 'gemini';
  temperature?: number;
  maxTokens?: number;
  tools?: string[];
  customInstructions?: string;
  // Add more fields as needed
}

export type AgentType = 'chat' | 'canvas' | 'insurance' | 'salary_viewer' | 'a2ui';
```

---

## 5. Dependencies

### Task Order (Frontend):
1. Add Settings navigation item (Task 1.1)
2. Create Settings page route (Task 1.2)
3. Create mock data service (Task 1.4)
4. Design and implement UI components (Task 1.3)
5. Add state management (Task 1.5)
6. Polish UI/UX (Task 1.6)

### External Dependencies:
- Shadcn UI components (already installed)
- React Hook Form (if not already installed)
- Lucide React icons (for settings icon)

---

## 6. Testing Strategy

### Frontend Testing (Current Phase):
- Manual testing of UI interactions
- Verify responsive design on different screen sizes
- Test keyboard navigation
- Validate form validation logic
- Verify mock data displays correctly

### Integration Testing (Future Phase):
- API endpoint tests
- End-to-end tests for settings flow
- Agent configuration application tests

---

## 7. Success Criteria

**Current Phase (Frontend-only):**
- ✅ Settings menu item appears in left navigation
- ✅ Settings page accessible and renders properly
- ✅ Agent settings list displays mock data
- ✅ Settings form allows editing (mock save)
- ✅ UI is polished and follows Shadcn UI patterns
- ✅ Responsive design works on all devices
- ✅ Code is well-structured for future backend integration

**Future Phase (With Backend):**
- Settings persist to database
- Settings apply to agent behavior
- Only admin users can access settings
- Real-time validation and error handling

---

## 8. Notes

- **Frontend-First Approach**: Build and refine UI/UX before implementing backend
- **Mock Data**: Use realistic mock data to test UI flows
- **Future-Proof**: Structure code to easily integrate with backend API later
- **Admin Only**: Plan for admin-only access (implement in backend phase)
- **Agent Types**: Consider different settings for different agent types
- **Extensibility**: Design settings structure to support new configuration options

---

## 9. Related Files

### Frontend Files to Create/Modify:
- Navigation component (add Settings item)
- `frontend/app/settings/page.tsx`
- `frontend/components/settings/agent-settings-list.tsx`
- `frontend/components/settings/agent-settings-card.tsx`
- `frontend/components/settings/agent-settings-form.tsx`
- `frontend/services/settings-mock.ts`
- `frontend/types/settings.ts`
- `frontend/stores/settings-store.ts` (optional)

### Backend Files (Future):
- `backend/api/routers/settings.py`
- `backend/services/settings_service.py`
- `backend/database/models.py` (add settings model)
- `backend/database/migrations/` (new migration)

---

## 10. Handoff Instructions

### For Frontend Agent:
1. Start with Task 1.1 (navigation item)
2. Use Shadcn UI components throughout
3. Follow existing patterns in the codebase
4. Create comprehensive mock data
5. Focus on UI/UX polish
6. Structure code for easy backend integration

### For Backend Agent (Future):
1. Review frontend implementation first
2. Design API contract based on frontend needs
3. Implement database schema
4. Create API endpoints
5. Integrate with agent registry
6. Update agent initialization logic

---

**Ready for Implementation**: Frontend Agent can start with Task 1.1
