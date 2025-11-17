# Development Requests & Task Management

## How This Workflow Works

This file serves as your centralized task management system. When you need new features, bug fixes, or improvements, add them here and I will analyze, plan, and execute them systematically.

### Workflow Steps

1. **Add Your Request**: Write your request in the "Pending Requests" section below
2. **Analysis**: I will analyze the request, understand requirements, and create a detailed plan
3. **Planning**: I will break down the task into subtasks and update the todo list
4. **Execution**: I will implement the changes following best practices
5. **Documentation**: I will update relevant documentation after completion
6. **Move to Completed**: The request will be moved to the "Completed Requests" section

### Request Template

When adding a new request, use this template:

```markdown
### [Request ID] - [Brief Title]

**Date Added**: YYYY-MM-DD
**Priority**: High / Medium / Low
**Category**: Feature / Bug Fix / Refactoring / Documentation / Testing

**Description**:
[Detailed description of what you need]

**Acceptance Criteria**:

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Notes**:
[Any additional context, constraints, or preferences]
```

---

## Pending Requests

[Add new requests here using the template above]

---

## In Progress Requests

[Requests currently being worked on will appear here]

---

## Completed Requests

### REQ-001 - Rename App from Rendezvous to 2-Aside

**Date Added**: 2025-01-19
**Date Completed**: 2025-01-19
**Priority**: Medium
**Category**: Refactoring

**Description**:
Changed the name of the app from "Rendezvous" to "2-Aside" and updated all reference texts across the entire frontend and backend codebase.

**Acceptance Criteria**:
- [x] All backend C# namespaces updated from `Rendezvous` to `TwoAside`
- [x] All frontend user-facing text updated to "2-Aside"
- [x] Configuration files updated (appsettings.json, app.json, package.json)
- [x] All 37 migration files updated
- [x] All documentation files updated
- [x] JWT configuration updated (Issuer, Audience)

**Summary of Changes**:
- **Backend (61 files)**:
  - Updated all C# namespaces from `Rendezvous` or `RendezvousApp.Backend` to `TwoAside.Backend`
  - Updated 13 controllers, 23 models, 8 services, 4 interfaces, 2 core files
  - Updated all 37 migration files with correct namespaces
  - Updated appsettings.json JWT configuration (Issuer: "2AsideApp", Audience: "2AsideAppUsers")

- **Frontend (10 files)**:
  - Updated app.json (name: "2-aside-p2p-betting")
  - Updated package.json (name: "2-aside-p2p-betting")
  - Updated all user-facing text in authentication, dashboard, games, profile, and funding pages
  - Changed "Welcome to Rendezvous" → "Welcome to 2-Aside"
  - Changed footer to "2-Aside v1.0.0" and "© 2024 2-Aside"

- **Documentation (4 files)**:
  - PROJECT.md: Title and description updated
  - ARCHITECTURE.md: All references updated, database name changed to "2AsideDB"
  - CONTEXT.md: Project name and database server updated
  - DEVELOPMENT_GUIDELINES.md: Example namespaces updated to TwoAside

**Total Files Updated**: 75+ files across the entire codebase

**Notes**:
- Folder/directory names kept as "Rendezvous" for backward compatibility
- File paths in documentation preserved
- All namespace changes follow C# conventions (TwoAside without hyphens)
- All user-facing text uses "2-Aside" with hyphen

---

## Request Categories

Use these categories to organize requests:

- **Feature**: New functionality or enhancement
- **Bug Fix**: Fixing broken or incorrect behavior
- **Refactoring**: Improving code structure without changing functionality
- **Documentation**: Adding or updating documentation
- **Testing**: Adding unit tests, integration tests, or E2E tests
- **Performance**: Optimizing speed or resource usage
- **Security**: Security improvements or vulnerability fixes
- **DevOps**: CI/CD, deployment, infrastructure improvements

---

## Priority Guidelines

- **High**: Critical bugs, security issues, blocking features
- **Medium**: Important features, non-critical bugs, performance improvements
- **Low**: Nice-to-have features, minor improvements, documentation

---

## Tips for Writing Good Requests

1. **Be Specific**: Clearly describe what you want and why
2. **Provide Context**: Include relevant background information
3. **Define Success**: Use acceptance criteria to define when the task is complete
4. **Include Examples**: If applicable, provide examples or mockups
5. **Note Constraints**: Mention any technical constraints or preferences
6. **Link Related Items**: Reference related files, issues, or requests

---

## Integration with Development

When you add a request here:

1. Tag me in the conversation and reference the request ID
2. I will analyze the request and create a detailed implementation plan
3. I will use the TodoWrite tool to track progress
4. I will update this file as work progresses
5. Upon completion, I will move the request to "Completed Requests" with a summary

---

## Current Development Focus

**Active Sprint**: N/A
**Current Tasks**: None
**Next Up**: Awaiting new requests

**Recent Completion**: REQ-001 - Successfully renamed app from Rendezvous to 2-Aside (75+ files updated)

---

## Notes

- Keep this file updated with new requests as they come up
- Archive old completed requests to a separate file if this gets too long
- Use GitHub issues or project management tools for larger teams
- This workflow is designed for solo development or small teams
