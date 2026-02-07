---
name: task-management
description: Manage project tasks, implementation plans, and walkthroughs using a standardized workflow.
---

# Task Management Skill

This skill provides a structured workflow for handling complex requests. Use it to ensure clarity, user approval, and proper documentation of your work.

## Core Principles

1.  **Clarity First**: Before writing code, ensure you understand the goal and have a plan.
2.  **User Alignment**: Get approval for significant changes using an implementation plan.
3.  **Traceability**: Keep a checklist of tasks to track progress.
4.  **Proof of Work**: Document what you did and how you verified it.

## The Workflow

### 1. Planning Phase
For any task that involves multiple steps or changes to several files:
- **Location**: Use the `data/tasks/` directory.
- **Task List**: Create or update `data/tasks/tasks.md` with a checklist of items.
- **Implementation Plan**: Create `data/tasks/implementation_plan.md`.
    - Outline the goal.
    - List proposed changes by component/file.
    - Detail the verification plan (tests, manual steps).
- **Approval**: Present the plan to the user and wait for confirmation.

### 2. Execution Phase
- Update `data/tasks/tasks.md` as you progress (use `[ ]`, `[/]`, `[x]`).
- If you find unexpected complexity, update the implementation plan or communicate with the user.

### 3. Verification & Handover
- **Validation**: Perform the steps in your verification plan.
- **Walkthrough**: Update or create `data/tasks/walkthrough.md`.
    - Summarize changes.
    - Provide logs, screenshots, or terminal outputs showing success.
- **Final Cleanup**: Delete any temporary test files or scripts created during verification (unless they are meant to be permanent tests).

## File Templates

### tasks.md
```markdown
# Task: [Description]

- [x] Completed task <!-- id: 0 -->
- [/] In progress task <!-- id: 1 -->
- [ ] Planned task <!-- id: 2 -->
```

### implementation_plan.md
```markdown
# Plan: [Goal Name]

## Proposed Changes
### [Component Name]
#### [MODIFY] [filename](file:///path/to/file)
- Change description

## Verification Plan
- Specific commands or steps to run
```

## Directory Structure
- `data/tasks/`: All MD files for the current session's work.
- `data/tasks/`: ONLY for temporary data, logs, or results that need to be deleted after completion.
