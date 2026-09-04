---
description: Create a branch from a ticket in your issue tracker, cut from the base branch
argument-hint: [ticket-id-or-url]
allowed-tools: Bash(git fetch:*), Bash(git status:*), Bash(git switch:*), Bash(git branch:*), Bash(git pull:*), Bash(git rev-parse:*), Bash(git ls-remote:*), Bash(git stash:*), Bash(git for-each-ref:*), Bash(python3:*), Read
---

# Start work on a ticket

## Repo context

- Current branch: !`git branch --show-current`
- Working tree: !`git status --short`
- Local branches: !`git branch --format='%(refname:short)'`

## Ticket

`$ARGUMENTS`

Use the `ticket-branch` skill to handle this end to end. If `$ARGUMENTS` is empty, follow the skill's guidance for resolving an unstated ticket rather than assuming one.
