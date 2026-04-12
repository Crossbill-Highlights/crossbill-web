---
name: start-github-ticket
description: Use when the user provides a GitHub issue/ticket URL (e.g. github.com/Crossbill-Highlights/crossbill-web/issues/NNN) and asks to start working on it — fetches the ticket, moves it to In Progress on the project board, sets up a worktree, and begins implementation.
---

# Start GitHub Ticket

Use this when the user drops a GitHub ticket URL and says "start working on this", "implement this", "pick this up", or similar.

## Steps

### 1. Fetch the ticket

Parse owner/repo/number from the URL and read the issue:

```bash
gh issue view <number> --repo Crossbill-Highlights/crossbill-web --json number,title,body,labels,projectItems,url
```

Read the full body carefully — that's the spec for what you're implementing.

### 2. Move ticket to "In Progress" on the project board

The issue's `projectItems` in the JSON output contains the project item id(s). Find the project and set the Status field to "In Progress":

```bash
# List projects to find the right one (usually only one)
gh project list --owner Crossbill-Highlights

# Get the Status field id and "In Progress" option id for the project
gh project field-list <project-number> --owner Crossbill-Highlights --format json

# Set the item status
gh project item-edit \
  --project-id <PROJECT_ID> \
  --id <ITEM_ID> \
  --field-id <STATUS_FIELD_ID> \
  --single-select-option-id <IN_PROGRESS_OPTION_ID>
```

If the issue isn't on the project board yet, add it first with `gh project item-add`.

If any of these commands fail (auth, TLS, missing permissions), report the failure to the user and ask whether to continue without the status update — don't silently skip it.

### 3. Create a worktree

Worktrees live in `.worktrees/` at the repo root. Use a short kebab-case slug derived from the issue title (match the style of existing entries like `escape-like-wildcards`, `ai-usage-tracking`). Branch name should be similar, optionally prefixed with the issue number.

```bash
# From the main repo root
git worktree add .worktrees/<slug> -b <branch-name>
```

### 4. Copy the .env file

The `.env` is git-ignored and not carried across worktrees. Copy it so the new worktree can run the stack:

```bash
cp .env .worktrees/<slug>/.env
```

If `.env` doesn't exist in main, tell the user and stop — don't fabricate one.

### 5. Begin implementation

`cd` into the worktree and start working on the ticket. Before writing code:

- Re-read the ticket body and acceptance criteria.
- If the task is non-trivial or ambiguous, invoke `superpowers:brainstorming` before touching code.
- Otherwise apply the usual project workflow (TDD where applicable, pyright/ruff on the backend, eslint/type-check on the frontend — see CLAUDE.md).

Reference the issue number in commits and the eventual PR so GitHub auto-links them (`Fixes #NNN`).

## Quick reference

| Step | Command |
|------|---------|
| Read ticket | `gh issue view <n> --repo Crossbill-Highlights/crossbill-web --json number,title,body,labels,projectItems` |
| Move to In Progress | `gh project item-edit --project-id … --id … --field-id … --single-select-option-id …` |
| Create worktree | `git worktree add .worktrees/<slug> -b <branch>` |
| Copy env | `cp .env .worktrees/<slug>/.env` |

## Common mistakes

- **Skipping the project board update silently** when `gh project` commands fail. Surface the failure instead.
- **Forgetting to copy `.env`** — the worktree will then fail to start the backend/frontend.
- **Creating the worktree outside `.worktrees/`** — keep everything under that directory so it stays consistent with existing ones.
- **Using a branch name that already exists** — check with `git branch --list` first if unsure.
