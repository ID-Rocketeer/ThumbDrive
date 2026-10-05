# Project Rules

## Rule #1: Strict Test-Driven Development (TDD)
- **Full Coverage Scope (Backend & Client)**: TDD applies equally to both backend code and client-side JavaScript/UI logic.
- **Failing Test First**: Always write a failing unit test (backend and/or client-side) before implementing any production code.
- **Client-Side Testing**: Use Node.js (`node --test`) with DOM/Web API mocks (or Python subprocess integration) to unit test frontend JavaScript functions, state transitions, Object URL lifecycles, and network request patterns.
- **Bug Fix Reproduction**: When fixing a bug in backend or frontend code, write a failing unit test that reproduces the issue before taking any corrective action.
- **Regression Prevention**: Ensure all existing unit tests pass once the bug fix or feature is complete.
- **Test Modification Approval**: Never modify an existing unit test during a bug fix without discussing and getting approval from the user first.

## Rule #2: Mandatory Design Discussion & Approval
- **Discuss Design First**: Always discuss, present proposed approaches, and get explicit user approval on design, UI, or architectural choices before implementing any code or style changes.

