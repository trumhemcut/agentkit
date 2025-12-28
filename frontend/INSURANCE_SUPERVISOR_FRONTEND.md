# Insurance Supervisor Frontend Implementation

## Overview
Frontend implementation for the Insurance Supervisor multi-agent system. This provides UI components to visualize specialist routing and agent delegation in real-time.

## Components Created

### 1. InsuranceSupervisorIndicator
**Location**: `frontend/components/InsuranceSupervisorIndicator.tsx`

A badge-based component that displays:
- Supervisor badge when routing
- Specialist badges (Policy, Claims, Quoting, Support) with Vietnamese names
- Active indicator (pulsing dot) during processing
- Color-coded specialist types

**Usage**:
```tsx
<InsuranceSupervisorIndicator 
  specialist="policy"
  isActive={true}
/>
```

### 2. Badge UI Component
**Location**: `frontend/components/ui/badge.tsx`

Standard Shadcn UI badge component with variants:
- `default` - Primary colored badge
- `secondary` - Secondary colored badge
- `destructive` - Destructive/error colored badge
- `outline` - Outlined badge

## Type Definitions

### AgentId Type
Added insurance-supervisor to valid agent IDs:
```typescript
export type AgentId = 'chat' | 'canvas' | 'a2ui' | 'insurance-supervisor';
```

### InsuranceSpecialist Type
```typescript
export type InsuranceSpecialist = 'policy' | 'claims' | 'quoting' | 'support';
```

### InsuranceSupervisorMetadata Interface
```typescript
export interface InsuranceSupervisorMetadata {
  selected_specialist?: InsuranceSpecialist;
  specialist_name?: string;
}
```

### Message Type Extension
Extended Message interface to include:
- `agentId` - Agent identifier
- `metadata` - Generic metadata object for agent-specific data

## Integration Points

### AgentSelector
Updated to include Shield icon for insurance-supervisor agent:
```tsx
case 'shield':
  return <Shield className="h-4 w-4 mr-2" />;
```

### AgentMessageBubble
Integrated InsuranceSupervisorIndicator to display specialist routing:
- Checks if message is from insurance-supervisor
- Extracts specialist from message metadata
- Shows routing indicator above message content

## Specialist Configuration

Each specialist has:
- **English Name**: For code/API use
- **Vietnamese Name**: For UI display
- **Icon**: Lucide icon component
- **Color**: Tailwind CSS color classes

| Specialist | Vietnamese Name | Icon | Color |
|------------|----------------|------|-------|
| policy | Chuyên gia Chính sách | FileText | Blue |
| claims | Chuyên gia Bồi thường | ClipboardList | Green |
| quoting | Chuyên gia Báo giá | DollarSign | Amber |
| support | Hỗ trợ Khách hàng | Headphones | Purple |

## Testing

✅ **Test suite fully configured and passing!**

Test suite created at `frontend/tests/insurance-supervisor.test.tsx` with complete Jest configuration.

### Test Results
```
Test Suites: 1 passed, 1 total
Tests:       13 passed, 13 total
```

### Installed Testing Dependencies
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom @types/jest ts-node
```

### Configuration Files
- `jest.config.ts` - Jest configuration with Next.js support
- `jest.setup.ts` - Setup file for @testing-library/jest-dom matchers

### Running Tests
```bash
npm test              # Run all tests
npm run test:watch    # Run tests in watch mode
```

### Test Coverage
All 13 tests passing:
- ✅ Supervisor badge rendering without specialist
- ✅ Policy specialist badge with Vietnamese name
- ✅ Claims specialist badge with Vietnamese name
- ✅ Quoting specialist badge with Vietnamese name
- ✅ Support specialist badge with Vietnamese name
- ✅ Active indicator shows when isActive=true
- ✅ Active indicator hidden when isActive=false
- ✅ Routing arrow displays between badges
- ✅ No routing arrow without specialist
- ✅ Correct color classes for policy specialist
- ✅ Correct color classes for claims specialist
- ✅ Correct color classes for quoting specialist
- ✅ Correct color classes for support specialist

## API Integration

The existing API service (`frontend/services/api.ts`) already supports the insurance-supervisor agent through dynamic agent ID routing. No changes needed.

## How It Works

1. **User sends message** with insurance-supervisor agent selected
2. **Backend routes** to appropriate specialist agent
3. **Backend includes metadata** with `selected_specialist` in events
4. **Frontend displays**:
   - Supervisor badge
   - Arrow (→)
   - Specialist badge with Vietnamese name
   - Pulsing indicator if actively processing
5. **Message renders** with specialist indicator above content

## Files Modified

- ✅ `frontend/types/agent.ts` - Added types
- ✅ `frontend/types/chat.ts` - Extended Message interface
- ✅ `frontend/components/AgentSelector.tsx` - Added shield icon
- ✅ `frontend/components/AgentMessageBubble.tsx` - Integrated indicator
- ✅ `frontend/components/InsuranceSupervisorIndicator.tsx` - New component
- ✅ `frontend/components/ui/badge.tsx` - New Shadcn UI component
- ✅ `frontend/tests/insurance-supervisor.test.tsx` - Test suite

## Next Steps

To complete the implementation:

1. **Backend must set metadata**: Ensure backend includes `selected_specialist` in message metadata
2. **Test end-to-end**: Run backend with insurance-supervisor agent and verify UI displays correctly
3. **Install testing deps**: Add testing libraries to run component tests
4. **Update knowledge base**: Document patterns in `.docs/2-knowledge-base/`

## Example Usage

When a user asks about insurance policies:
```
User: "What are the benefits of life insurance?"

Backend: Routes to policy specialist
         Returns metadata: { selected_specialist: "policy" }

Frontend: Displays:
┌─────────────────────────────────────────┐
│ [Shield Supervisor] → [FileText Chuyên gia Chính sách] ● │
├─────────────────────────────────────────┤
│ Life insurance provides financial        │
│ protection for your beneficiaries...     │
└─────────────────────────────────────────┘
```

## Notes

- Vietnamese names used for user-facing labels
- Color coding helps users quickly identify specialist type
- Pulsing indicator shows real-time processing status
- Component is fully typed with TypeScript
- Follows Shadcn UI design patterns
- Compatible with existing AG-UI protocol
