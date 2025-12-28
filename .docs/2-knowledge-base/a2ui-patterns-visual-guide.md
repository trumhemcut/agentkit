# A2UI Tool-Calling Patterns - Visual Guide

## Pattern 1: Basic A2UI Agent (Single Tool Call)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                              │
│        "Create a checkbox for agreeing to terms"            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   LLM with Tools Bound       │
        │  (qwen:7b + create_checkbox) │
        └──────────────┬───────────────┘
                       │
                       │ Analyzes request
                       │ Decides tool to call
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Tool Call: create_checkbox │
        │   Args: {                    │
        │     label: "I agree to terms"│
        │     checked: false           │
        │   }                          │
        └──────────────┬───────────────┘
                       │
                       │ Executes tool
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Component Generated        │
        │   ID: checkbox-abc123        │
        │   Type: checkbox             │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   A2UI Protocol Messages     │
        │   - SurfaceUpdate            │
        │   - DataModelUpdate          │
        │   - BeginRendering           │
        └──────────────┬───────────────┘
                       │
                       ▼
                    ✅ DONE
                 (1 component)
                  ~1-2 seconds
                  ~500-1000 tokens
```

## Pattern 2: A2UI Agent with Loop (Multiple Tool Calls)

```
┌────────────────────────────────────────────────────────────────┐
│                       USER REQUEST                             │
│  "Create a signup form with email, password, and submit button"│
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  LLM with Tools Bound        │
        │  (qwen:7b + all tools)       │
        └──────────────┬───────────────┘
                       │
                       │ ╔════════════════════════════╗
                       │ ║  LOOP ITERATION 1          ║
                       ▼ ╚════════════════════════════╝
        ┌──────────────────────────────┐
        │   LLM Reasoning:             │
        │   "I need email input first" │
        │                              │
        │   Tool Call:                 │
        │   create_textinput(          │
        │     label="Email",           │
        │     placeholder="Enter email"│
        │   )                          │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Tool Result:               │
        │   "Created textinput-abc123" │
        └──────────────┬───────────────┘
                       │
                       │ ╔════════════════════════════╗
                       │ ║  LOOP ITERATION 2          ║
                       ▼ ╚════════════════════════════╝
        ┌──────────────────────────────┐
        │   LLM Sees Previous Result   │
        │   LLM Reasoning:             │
        │   "Now password input"       │
        │                              │
        │   Tool Call:                 │
        │   create_textinput(          │
        │     label="Password",        │
        │     placeholder="Password"   │
        │   )                          │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Tool Result:               │
        │   "Created textinput-def456" │
        └──────────────┬───────────────┘
                       │
                       │ ╔════════════════════════════╗
                       │ ║  LOOP ITERATION 3          ║
                       ▼ ╚════════════════════════════╝
        ┌──────────────────────────────┐
        │   LLM Sees Previous Results  │
        │   LLM Reasoning:             │
        │   "Finally, submit button"   │
        │                              │
        │   Tool Call:                 │
        │   create_button(             │
        │     label="Sign Up",         │
        │     action="submit"          │
        │   )                          │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Tool Result:               │
        │   "Created button-ghi789"    │
        └──────────────┬───────────────┘
                       │
                       │ ╔════════════════════════════╗
                       │ ║  LOOP ITERATION 4          ║
                       ▼ ╚════════════════════════════╝
        ┌──────────────────────────────┐
        │   LLM Sees All Results       │
        │   LLM Reasoning:             │
        │   "All components created.   │
        │    Task complete."           │
        │                              │
        │   No Tool Calls              │
        │   → LOOP ENDS                │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Collect All Components:    │
        │   1. textinput-abc123 (email)│
        │   2. textinput-def456 (pwd)  │
        │   3. button-ghi789 (submit)  │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   A2UI Protocol Messages     │
        │   - SurfaceUpdate (3 comps)  │
        │   - DataModelUpdate          │
        │   - BeginRendering           │
        └──────────────┬───────────────┘
                       │
                       ▼
                    ✅ DONE
                 (3 components)
                  ~4-8 seconds
                  ~2000-4000 tokens
```

## Conversation Flow (Loop Pattern)

Here's what the conversation looks like internally:

```
┌─────────────────────────────────────────────────────────────┐
│  Conversation: [                                            │
│    SystemMessage("You are a UI generator..."),             │
│    HumanMessage("Create signup form..."),                  │
│                                                             │
│    # Loop iteration 1                                      │
│    AIMessage(                                              │
│      content="I'll create email input",                    │
│      tool_calls=[{                                         │
│        name: "create_textinput",                           │
│        args: {label: "Email"}                              │
│      }]                                                    │
│    ),                                                      │
│    ToolMessage("Created textinput-abc123"),               │
│                                                             │
│    # Loop iteration 2                                      │
│    AIMessage(                                              │
│      content="Now password input",                         │
│      tool_calls=[{                                         │
│        name: "create_textinput",                           │
│        args: {label: "Password"}                           │
│      }]                                                    │
│    ),                                                      │
│    ToolMessage("Created textinput-def456"),               │
│                                                             │
│    # Loop iteration 3                                      │
│    AIMessage(                                              │
│      content="Finally submit button",                      │
│      tool_calls=[{                                         │
│        name: "create_button",                              │
│        args: {label: "Sign Up"}                            │
│      }]                                                    │
│    ),                                                      │
│    ToolMessage("Created button-ghi789"),                  │
│                                                             │
│    # Loop iteration 4 - LLM decides to stop               │
│    AIMessage("All components created. Done.")              │
│  ]                                                         │
└─────────────────────────────────────────────────────────────┘
```

## ReAct Pattern Breakdown

```
  ╔═══════════════════════════════════════════════════════╗
  ║                   REACT LOOP                          ║
  ╚═══════════════════════════════════════════════════════╝

  ┌─────────────┐
  │   REASON    │  ← LLM analyzes request and decides action
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │    ACT      │  ← Execute tool(s)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  OBSERVE    │  ← See tool result(s)
  └──────┬──────┘
         │
         ▼
      ┌───┴────┐
      │ Done?  │
      └───┬────┘
          │
    ┌─────┴─────┐
   No          Yes
    │            │
    └────┐   ┌───┘
         │   │
         │   ▼
         │  END
         │
         └─→ REPEAT (go back to REASON)
```

## LangGraph Structure Comparison

### Basic A2UI Graph
```
    START
      │
      ▼
  ┌─────────┐
  │  agent  │
  └────┬────┘
       │
       ▼
      END
```

### A2UI Loop Graph (Internal Loop)
```
    START
      │
      ▼
  ┌──────────────┐
  │  loop_agent  │  ← Contains internal tool-calling loop
  │              │
  │  ╔═══════╗  │
  │  ║ LOOP  ║  │  LLM → Tool → LLM → Tool → ... → Done
  │  ╚═══════╝  │
  └──────┬───────┘
         │
         ▼
        END
```

### A2UI Loop Graph (Explicit ToolNode) - Future Option
```
      START
        │
        ▼
    ┌───────┐
    │ agent │ ← Decides tool or finish
    └───┬───┘
        │
        ▼
   ┌────┴────┐
   │ continue?│
   └────┬────┘
        │
   ┌────┴────┐
   │         │
  Yes       No
   │         │
   ▼         ▼
┌──────┐   END
│ tools│
└──┬───┘
   │
   └─→ (loop back to agent)

# Agent sees tool results and decides next action
```

## Performance Comparison

```
┌──────────────────────────────────────────────────────────┐
│  METRIC COMPARISON                                       │
├──────────────────┬──────────────┬────────────────────────┤
│                  │ Basic Agent  │ Loop Agent             │
├──────────────────┼──────────────┼────────────────────────┤
│ LLM Calls        │      1       │    4 (for 3 comps)     │
│ Token Usage      │   ~750       │   ~3000                │
│ Latency          │   1-2s       │   4-8s                 │
│ Cost (per req)   │   $0.0001    │   $0.0004              │
│ Components       │    1         │   1-N                  │
└──────────────────┴──────────────┴────────────────────────┘

                    ▲              ▲
                  Better         Better for
                for simple       complex UIs
                  UIs
```

## Decision Tree

```
                  User Request
                       │
                       ▼
          ┌────────────────────────┐
          │ Need multiple          │
          │ components?            │
          └─────┬──────────────┬───┘
                │              │
               No             Yes
                │              │
                ▼              ▼
     ┌──────────────┐   ┌─────────────┐
     │ Basic Agent  │   │ Loop Agent  │
     │              │   │             │
     │ • Fast       │   │ • Powerful  │
     │ • Cheap      │   │ • Flexible  │
     │ • Simple     │   │ • Slower    │
     └──────────────┘   └─────────────┘
            ▲                  ▲
            │                  │
     Use for 90%        Use for 10%
     of requests        of requests
```

## Summary Table

```
╔═══════════════════════════════════════════════════════════╗
║             WHEN TO USE WHICH PATTERN                     ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Basic Agent:                                             ║
║  ✅ "Create a checkbox"                                    ║
║  ✅ "Add a button for submit"                              ║
║  ✅ "Show me a text input"                                 ║
║                                                           ║
║  Loop Agent:                                              ║
║  ✅ "Create a form with email, password, and button"       ║
║  ✅ "Build a settings panel with 5 options"                ║
║  ✅ "Generate a dashboard with chart and controls"         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```
