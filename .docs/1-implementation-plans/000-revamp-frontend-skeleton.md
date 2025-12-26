# Implementation Plan: Frontend Architecture Skeleton

**Status:** Draft  
**Created:** 2025-12-26  
**Requirement:** [000-revamp-frontend-skeleton.md](../0-requirements/000-revamp-frontend-skeleton.md)

## Overview

Create a clean frontend architecture skeleton using Shadcn UI + NextJS to demonstrate the component library and layout structure. This will serve as the foundation for the AgentKit UI, showcasing:
- Full-height left sidebar navigation
- Header component
- Main content area with common Shadcn UI components (label, input, checkbox, combobox, select, table/grid, etc.)
- **Must use Shadcn's default styling** (no custom theme overrides)

## Goals

1. Establish a clean, professional layout structure with sidebar + header + main content
2. Demonstrate all commonly used Shadcn UI components in one showcase page
3. Use Shadcn's default theme and styling without customization
4. Create reusable layout components that can be used throughout the application

## Non-Goals

- Backend integration (this is purely UI skeleton)
- Agent/AG-UI protocol (no agent communication needed)
- Custom theming or design system (use Shadcn defaults)
- Functional features (showcase only)

---

## Implementation Tasks

### Phase 1: Layout Structure Setup

#### Task 1.1: Create Base Layout Components
**Owner:** Frontend Agent  
**Dependencies:** None

Create the foundational layout structure:

**Files to Create/Modify:**
- `frontend/components/Layout/AppLayout.tsx` - Main application layout wrapper
- `frontend/components/Layout/Sidebar.tsx` - Left navigation sidebar (100% height)
- `frontend/components/Layout/Header.tsx` - Top header bar
- `frontend/components/Layout/MainContent.tsx` - Main content area wrapper

**Requirements:**
- AppLayout should use flexbox/grid for proper layout structure
- Sidebar should be fixed, taking 100% viewport height
- Sidebar should have a fixed width (e.g., 240px or 280px)
- Header should span the remaining width (full width minus sidebar)
- MainContent should be scrollable with proper padding
- Use Tailwind CSS classes that align with Shadcn's design patterns

**Acceptance Criteria:**
- [ ] Layout renders correctly at various viewport sizes
- [ ] Sidebar remains fixed at 100% height
- [ ] Header and main content fill remaining horizontal space
- [ ] No custom CSS needed, only Tailwind + Shadcn defaults

---

### Phase 2: Shadcn Component Integration

#### Task 2.1: Install Required Shadcn Components
**Owner:** Frontend Agent  
**Dependencies:** Task 1.1

Install all Shadcn UI components needed for the showcase:

```bash
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add label
npx shadcn@latest add checkbox
npx shadcn@latest add select
npx shadcn@latest add combobox
npx shadcn@latest add dropdown-menu
npx shadcn@latest add table
npx shadcn@latest add card
npx shadcn@latest add separator
npx shadcn@latest add badge
npx shadcn@latest add switch
npx shadcn@latest add radio-group
npx shadcn@latest add textarea
```

**Note:** Do NOT modify the generated component files - use them as-is with default styling.

**Acceptance Criteria:**
- [ ] All components installed in `frontend/components/ui/`
- [ ] No modifications to generated Shadcn component files
- [ ] TypeScript types are correctly imported

---

#### Task 2.2: Create Component Showcase Page
**Owner:** Frontend Agent  
**Dependencies:** Task 2.1

Create a demonstration page that showcases all installed components:

**Files to Create/Modify:**
- `frontend/app/showcase/page.tsx` - Main showcase page
- `frontend/components/Showcase/ComponentSection.tsx` - Reusable section wrapper for each component group

**Page Structure:**
```
├── Form Controls Section
│   ├── Label + Input examples
│   ├── Textarea
│   ├── Checkbox group
│   ├── Radio group
│   ├── Switch examples
├── Selection Section
│   ├── Select (Dropdown)
│   ├── Combobox
├── Data Display Section
│   ├── Table with sample data
│   ├── Card examples
│   ├── Badge examples
├── Interactive Section
│   ├── Button variants (default, outline, ghost, destructive)
│   ├── Dropdown Menu
```

**Requirements:**
- Each component section should have a heading
- Include 2-3 examples per component showing different variants/states
- Use Card components to group related examples
- Add Separator between major sections
- Include descriptive Label components for each example
- Add sample data for Table (e.g., 5-10 rows of mock user data)

**Acceptance Criteria:**
- [ ] All installed components are demonstrated
- [ ] Each component shows multiple variants/states
- [ ] Page is well-organized with clear sections
- [ ] Uses only Shadcn default styling
- [ ] Page is responsive and looks good on different screen sizes

---

#### Task 2.3: Populate Sidebar Navigation
**Owner:** Frontend Agent  
**Dependencies:** Task 1.1, Task 2.2

Add navigation items to the sidebar:

**Requirements:**
- Add navigation links to showcase page and other placeholder pages
- Use Shadcn Button component (variant="ghost") for nav items
- Include icons (use lucide-react icons)
- Highlight active navigation item
- Add a logo/title at the top of sidebar

**Example Navigation Items:**
- Dashboard (home icon)
- Component Showcase (layout icon)
- Agents (bot icon)
- Settings (settings icon)

**Acceptance Criteria:**
- [ ] Sidebar shows clear navigation structure
- [ ] Active item is visually distinct
- [ ] Icons are properly aligned with text
- [ ] Hover states work correctly
- [ ] Uses Shadcn default button styling

---

#### Task 2.4: Implement Header Component
**Owner:** Frontend Agent  
**Dependencies:** Task 1.1

Add content to the header bar:

**Requirements:**
- Add page title/breadcrumb
- Add user profile section on the right (Avatar + Dropdown Menu)
- Include theme toggle placeholder (for future implementation)
- Use Shadcn Avatar and Dropdown Menu components

**Acceptance Criteria:**
- [ ] Header displays current page title
- [ ] User menu is aligned to the right
- [ ] Header has proper spacing and padding
- [ ] Uses Shadcn default styling

---

### Phase 3: Integration and Polish

#### Task 3.1: Update Main App Entry Point
**Owner:** Frontend Agent  
**Dependencies:** Task 1.1, Task 2.2, Task 2.3, Task 2.4

Update the main app page to use the new layout:

**Files to Modify:**
- `frontend/app/page.tsx` - Use AppLayout and redirect to showcase
- `frontend/app/layout.tsx` - Update root layout if needed

**Requirements:**
- Wrap app content with AppLayout component
- Set showcase page as the default landing page
- Ensure proper TypeScript types throughout

**Acceptance Criteria:**
- [ ] App renders with new layout structure
- [ ] Default page shows component showcase
- [ ] No console errors or TypeScript errors
- [ ] Hot reload works correctly during development

---

#### Task 3.2: Documentation
**Owner:** Frontend Agent  
**Dependencies:** All previous tasks

Update documentation:

**Files to Create/Modify:**
- `frontend/README.md` - Add section about layout structure
- `.docs/2-knowledge-base/frontend-layout-patterns.md` - Document the layout pattern

**Content to Include:**
- How to use AppLayout component
- Sidebar navigation patterns
- Component showcase organization
- Link to Shadcn UI documentation

**Acceptance Criteria:**
- [ ] README updated with layout usage
- [ ] Knowledge base includes layout patterns
- [ ] Code examples are included

---

## Technical Specifications

### Layout Structure

```tsx
<AppLayout>
  <Sidebar />
  <div className="flex-1 flex flex-col">
    <Header />
    <MainContent>
      {/* Page content */}
    </MainContent>
  </div>
</AppLayout>
```

### Component Showcase Organization

Each component section should follow this pattern:

```tsx
<Card>
  <CardHeader>
    <CardTitle>Component Name</CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    <div>
      <Label>Example 1</Label>
      {/* Component demo */}
    </div>
    <div>
      <Label>Example 2</Label>
      {/* Component demo */}
    </div>
  </CardContent>
</Card>
```

---

## Testing Checklist

- [ ] Layout renders correctly in Chrome, Firefox, Safari
- [ ] Sidebar maintains 100% height at all viewport sizes
- [ ] All Shadcn components render without errors
- [ ] No TypeScript compilation errors
- [ ] No console warnings
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Navigation links are clickable (even if they go to placeholder pages)
- [ ] All component variants are demonstrated
- [ ] Default Shadcn styling is preserved throughout

---

## Dependencies

**Frontend:**
- NextJS (already installed)
- Shadcn UI components (to be installed via CLI)
- Tailwind CSS (already configured)
- lucide-react (for icons)

**No Backend Dependencies** - This is purely a frontend UI skeleton

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Custom styling accidentally overrides Shadcn defaults | Code review to ensure only Tailwind utility classes are used |
| Layout breaks on smaller screens | Test responsive behavior early and often |
| Component installation issues | Follow Shadcn installation docs exactly |
| Too many components making page cluttered | Use Cards and Separators to organize content clearly |

---

## Success Criteria

1. ✅ Single page application with left sidebar (100% height), header, and main content
2. ✅ All common Shadcn UI components are demonstrated
3. ✅ Uses Shadcn's default styling without customization
4. ✅ Clean, professional layout that can serve as foundation for AgentKit UI
5. ✅ Fully responsive design
6. ✅ Zero TypeScript/runtime errors
7. ✅ Documentation updated with layout patterns

---

## References

- [Shadcn UI Documentation](https://ui.shadcn.com/)
- [NextJS App Router Documentation](https://nextjs.org/docs/app)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- Frontend Agent Guide: [.github/agents/frontend.agent.md](../../.github/agents/frontend.agent.md)
