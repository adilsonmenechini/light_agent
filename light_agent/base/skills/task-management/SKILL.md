---
name: task-management
description: Manage project tasks, implementation plans, and walkthroughs using a standardized workflow with verification patterns.
---

# Task Management Skill

Structured workflow for handling complex requests. Ensures clarity, user approval, and proper documentation.

## Core Principles

1. **Clarity First**: Before writing code, ensure you understand the goal and have a plan.
2. **User Alignment**: Get approval for significant changes using an implementation plan.
3. **Traceability**: Keep a checklist of tasks to track progress.
4. **Proof of Work**: Document what you did and how you verified it.

## The Workflow

### 1. Planning Phase
For any task that involves multiple steps or changes to several files:
- **Location**: Use the `data/tasks/` directory.
- **Task List**: Create or update `data/tasks/tasks.md` with a checklist.
- **Implementation Plan**: Create `data/tasks/implementation_plan.md`.
    - Outline the goal and scope.
    - List proposed changes by component/file.
    - Detail the verification plan (tests, manual steps).
    - Identify potential risks and mitigations.
- **Approval**: Present the plan to the user and wait for confirmation.

### 2. Execution Phase
- Update `data/tasks/tasks.md` as you progress using `[ ]`, `[/]`, `[x]`.
- If you find unexpected complexity, update the plan or communicate with the user.
- Mark items as `[/]` when actively working on them.

### 3. Verification & Handover
- **Validation**: Execute every step in your verification plan.
- **Walkthrough**: Update or create `data/tasks/walkthrough.md`.
    - Summarize all changes made.
    - Provide concrete evidence (logs, test outputs, screenshots).
    - Document any issues encountered and how they were resolved.
- **Final Cleanup**: Remove temporary test files/scripts unless they are permanent tests.

## File Templates

### tasks.md
```markdown
# Task: [Description]

Started: YYYY-MM-DD HH:MM

## Progress
- [x] Task 1 completed       <!-- id: 0 -->
- [/] Task 2 in progress     <!-- id: 1 -->
- [ ] Task 3 pending         <!-- id: 2 -->

## Notes
<!-- Add context, blockers, discoveries -->
```

### implementation_plan.md
```markdown
# Plan: [Goal Name]

## Goal
Clear statement of what we're achieving.

## Scope
- **In Scope**: What will be done
- **Out of Scope**: What will NOT be done

## Proposed Changes

### [Component/File 1]
#### [MODIFY] [filename](file:///path/to/file)
- Specific change 1
- Specific change 2

### [Component/File 2]
#### [CREATE] [filename](file:///path/to/new/file)
- New functionality

## Verification Plan
### Automated Tests
```bash
pytest tests/ --tb=short
```

### Manual Testing
1. Step-by-step manual verification
2. Edge case checks

### Expected Outcomes
- Test pass rate: 100%
- No new lint errors
- Build succeeds

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Risk 1 | High | Mitigation approach |

## Timeline
Estimate: X hours/days
```

### walkthrough.md
```markdown
# Walkthrough: [Goal Name]

Completed: YYYY-MM-DD HH:MM

## Summary
Brief overview of changes made.

## Changes Made

### File 1: [path/to/file](file:///path/to/file)
- Change description

### File 2: [path/to/file](file:///path/to/file)
- Change description

## Verification Results

### Automated Tests
```
$ pytest tests/ --tb=short
========================= 15 passed =========================
```

### Manual Verification
- [x] Verified feature X works
- [x] Verified error handling for edge case Y

## Issues Encountered
- Issue 1: How it was resolved
- Issue 2: Workaround applied

## Next Steps
- Recommended follow-up tasks
- Known limitations
```

## Directory Structure

```
data/tasks/
├── tasks.md                  # Master task list
├── implementation_plan.md    # Pre-execution planning
├── walkthrough.md           # Post-execution documentation
├── tests/                   # Temporary test files (delete after)
└── outputs/                 # Generated outputs (keep or delete)
```
