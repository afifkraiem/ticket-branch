# ticket-branch

A Claude skill that creates a git branch from a ticket — in whatever issue tracker your team uses — and moves the ticket to in-progress.

```
› start PROJ-412

  Ticket   PROJ-412 · Le résumé PDF plante à l'export
  Branch   fix/PROJ-412-le-resume-pdf-plante-a-l-export ← develop
  Status   Backlog → In Progress
```

Works with any tracker reachable over MCP. Jira, Linear, ClickUp, GitHub Issues, GitLab, Asana, Shortcut, Notion, Azure DevOps, YouTrack, Monday and Trello have documented mappings; others usually work from their tool descriptions alone, and adding one is a short entry in a reference file.

## Why

Branch naming is the kind of convention every team agrees on and nobody applies consistently. Once branch names are derived from the tracker rather than typed by hand, you get traceability from a commit back to the ticket for free, and nobody has to remember whether it's `feature/` or `feat/` this week.

## Install

**As a plugin** (recommended — gives you `/plugin update` and auto-updates):

```
/plugin marketplace add afifkraiem/ticket-branch
/plugin install ticket-branch@afifkraiem-plugins
```

Installed as a plugin, the optional slash command is namespaced: `/ticket-branch:branch`. The skill itself still triggers on plain language.

**As a project skill** — commit it into your own repo, everyone working on it gets it:

```bash
mkdir -p .claude/skills
cp -r skills/ticket-branch .claude/skills/
cp -r commands/branch.md .claude/commands/   # optional /branch shortcut
```

**As a personal skill** — available in all your repos:

```bash
mkdir -p ~/.claude/skills
cp -r skills/ticket-branch ~/.claude/skills/
```

You also need an MCP server for your tracker connected to Claude Code. Run `/mcp` to check what's connected.

Step-by-step setup, first run, and troubleshooting: **[GUIDE.md](GUIDE.md)**.

## Use

The skill triggers on its own when you're starting a ticket, so plain language works:

```
start PROJ-412
create a branch for https://linear.app/acme/issue/ENG-88
I'm picking up #217
```

Or use the slash command if you installed it: `/branch PROJ-412`.

To pin your team's conventions, ask Claude to set it up — it reads your recent branch names and proposes a config matching what you already do:

```
standardize our branch naming for this repo
```

## Configure

Optional. Without a config, the skill cuts from `develop` (falling back to your default branch) and names branches `{type}/{id}-{slug}`.

To pin it, drop a `.ticket-branch.json` at the repo root:

```json
{
  "baseBranch": "develop",
  "branchTemplate": "{type}/{id}-{slug}",
  "inProgressStatus": "In Progress",
  "assignSelf": true
}
```

Every key is optional. `skills/ticket-branch/references/config.md` documents the full schema, and `skills/ticket-branch/assets/ticket-branch.example.json` lists every key at its default.

## What it won't do without asking

- Touch a dirty working tree — it stops and offers to stash or commit.
- Rebase or merge a diverged base branch — it reports and waits.
- Push the branch, unless `push: true` or you ask.
- Post comments on tickets, unless `commentOnTicket: true`.

Local branch creation is reversible; anything your teammates can see is opt-in.

## Adding a tracker

`skills/ticket-branch/references/providers.md` holds one section per tracker. Two questions cover most of a new entry: where does the issue type live (native field, labels, or nowhere), and how is in-progress expressed (a status field, a workflow-state category, a section, or a list). PRs adding a tracker are welcome, ideally with the tool names you actually saw in your `/mcp` output.

## Layout

```
.claude-plugin/                       marketplace + plugin manifests
GUIDE.md                              user guide: install, first run, troubleshooting
PUBLISHING.md                         how this repo is distributed
skills/ticket-branch/
├── SKILL.md                          workflow
├── references/providers.md           per-tracker tool names and field mappings
├── references/config.md              config schema and examples
├── scripts/branch_name.py            deterministic slug + name builder
└── assets/ticket-branch.example.json
commands/branch.md                    optional /branch slash command
```

`branch_name.py` is Python 3.8+, standard library only, and usable on its own:

```bash
python3 skills/ticket-branch/scripts/branch_name.py \
  --id PROJ-123 --title "[BUG] Le résumé PDF plante" --type fix
# fix/PROJ-123-le-resume-pdf-plante
```

## Publishing a fork

This repo is both a plugin marketplace and the plugin. If you fork it, replace the `afifkraiem` placeholders in `.claude-plugin/` and `LICENSE` first — see [PUBLISHING.md](PUBLISHING.md).

## License

MIT
