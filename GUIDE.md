# User guide

How to install `ticket-branch`, run it for the first time, and pin your team's conventions.

- [Prerequisites](#prerequisites)
- [Step 1 — connect your tracker](#step-1--connect-your-tracker)
- [Step 2 — install the skill](#step-2--install-the-skill)
- [Step 3 — first run](#step-3--first-run)
- [Everyday use](#everyday-use)
- [Pinning your team's conventions](#pinning-your-teams-conventions)
- [What it asks before acting](#what-it-asks-before-acting)
- [Troubleshooting](#troubleshooting)
- [Updating and uninstalling](#updating-and-uninstalling)

## Prerequisites

- Claude Code, run from inside a git repository with a remote.
- An MCP server for your issue tracker. This is the one piece the skill can't provide — it reads your tickets through your tracker's MCP.
- Python 3.8 or later on your `PATH`, for the branch-name script. `python3 --version` to check.

## Step 1 — connect your tracker

Check what you already have. Inside a Claude Code session:

```
/mcp
```

If your tracker is listed as `connected`, skip to step 2.

Otherwise add it. Most trackers publish a hosted MCP server you connect over HTTP:

```bash
claude mcp add --transport http --scope user clickup https://mcp.clickup.com/mcp
```

Swap the name and URL for your tracker — Linear, Notion, Sentry and others publish equivalent endpoints, and self-hosted Jira or GitLab will have their own. The scope flag decides who gets it:

| Scope | Effect |
|---|---|
| `--scope user` | you, in all your repos — usually what you want for a tracker |
| `--scope project` | written to `.mcp.json` in the repo, so teammates inherit it on commit |
| `--scope local` | you, in this repo only (the default) |

Hosted servers generally use OAuth, so the first tool call opens a browser to authorize. Verify with:

```bash
claude mcp list
```

A server showing `failed` with a 401 means the credentials didn't take — re-run the auth flow from `/mcp` before going further.

## Step 2 — install the skill

**As a plugin** is the least work and the only route that updates itself:

```
/plugin marketplace add afifkraiem/ticket-branch
/plugin install ticket-branch@afifkraiem-plugins
```

If the install summary says `Run /reload-plugins to activate.`, run that. One thing changes versus the copy routes below: plugin commands are namespaced, so the optional shortcut is `/ticket-branch:branch` rather than `/branch`. The skill triggers on plain language either way.

Later, `/plugin update ticket-branch@afifkraiem-plugins` picks up new versions, and `/plugin marketplace update` refreshes the catalog.

**Per project**, copied and committed so the whole team gets it without installing anything:

```bash
mkdir -p .claude/skills .claude/commands
cp -r path/to/ticket-branch/skills/ticket-branch .claude/skills/
cp path/to/ticket-branch/commands/branch.md .claude/commands/   # optional
git add .claude && git commit -m "add ticket-branch skill"
```

**Personal**, available in every repo you work in:

```bash
mkdir -p ~/.claude/skills
cp -r path/to/ticket-branch/skills/ticket-branch ~/.claude/skills/
```

The two can coexist. Install it personally while you evaluate it, then commit it to the repo once the team agrees on the conventions.

Confirm it registered by starting a session and running `/context` — skills appear in the listing. Or just try step 3.

## Step 3 — first run

Pick a real ticket and ask in plain language:

```
› start CU-90x1abcd
```

You should see something like:

```
  Ticket   CU-90x1abcd · Le panier se vide au changement de langue
  Branch   fix/CU-90x1abcd-le-panier-se-vide-au-changement-de-langue ← develop
  Status   to do → en cours
```

Read the branch name it announces before it creates anything. If the shape isn't what your team wants, say so in the same breath — "use feat instead of feature" or "drop the type prefix" — and then write it down as config (next section) so you don't repeat yourself.

On a first run the tracker MCP may prompt for authorization mid-task. That's normal; approve it and the run continues.

## Everyday use

The skill triggers on intent, so there's no command to memorize. All of these work:

```
start PROJ-412
create a branch for https://linear.app/acme/issue/ENG-88
je prends le ticket CU-90x1abcd
I'm picking up #217
branche pour cette issue, elle est urgente
```

If you installed the slash command, `/branch PROJ-412` does the same thing explicitly. It's useful when you want to be sure — the slash command names the skill directly rather than relying on the phrasing being recognized.

You can override any part of the convention inline for a one-off:

```
start PROJ-412 but branch off release/2.4 instead
start PROJ-412, and push it so I can open a draft PR
```

## Pinning your team's conventions

Without config, the skill cuts from `develop` (falling back to your default branch) and names branches `{type}/{id}-{slug}`. To pin something else, ask:

```
› standardize branch naming for this repo
```

It reads your last 50 branch names, infers the convention already in use, and proposes a config. That's usually faster and more accurate than specifying one from scratch, since most teams have a de facto pattern nobody has written down.

The result is a `.ticket-branch.json` at the repo root. Commit it — that's what makes everyone's branches match:

```json
{
  "baseBranch": "develop",
  "branchTemplate": "{type}/{id}-{slug}",
  "inProgressStatus": "en cours",
  "assignSelf": true
}
```

Every key is optional; `references/config.md` has the full schema. Two worth setting early:

`inProgressStatus` — status names are per-list and per-project, so left unset the skill infers one from your workflow. Naming it explicitly removes a guess and a possible question on every run.

`provider` — only needed if you have more than one tracker MCP connected. `PROJ-123` is ambiguous between Jira, Linear, Shortcut and YouTrack, and without this the skill has to ask which one you meant.

## What it asks before acting

The skill stops and waits in these cases, by design:

| Situation | Why it stops |
|---|---|
| Uncommitted changes | switching branches would either fail or carry your work onto the new branch |
| Base branch diverged from the remote | rebase vs merge is a call about your local commits, not one to make for you |
| The ticket already has a branch | it matches on ticket ID, so it catches branches named under an older convention — it offers to switch rather than create a second one |
| Two labels imply different types | with no native issue type to break the tie, a wrong prefix ends up in your release notes |
| Several trackers connected, ambiguous ID | the project key means something to you and nothing to the skill |

It won't push the branch, comment on the ticket, or assign it unless your config says so or you ask. Creating a local branch is trivially undone; anything your teammates can see is opt-in.

## Troubleshooting

**"No tracker MCP connected."** `/mcp` shows nothing, or your server shows `failed`. Re-run step 1. If the server is connected but the skill doesn't find it, the tool names may be unusual — tell the skill which server to use ("use the acme-jira server") and consider adding an entry to `references/providers.md`.

**Nothing happens on "start PROJ-412".** The skill didn't trigger. Use `/branch PROJ-412` if you installed the command, or say "use the ticket-branch skill to start PROJ-412". If it happens often, the `description` in `SKILL.md` is what governs triggering and can be tuned.

**Wrong branch prefix.** The type came from the wrong signal. Check the ticket's native type first, then its labels — the skill prefers the native type. Fix it durably by editing `typeMap` in your config rather than correcting each run.

**Branch name too long, or truncated oddly.** Set `slugMaxLength`. It cuts on a word boundary, so the effective length lands at or below your number, not exactly on it.

**"not a valid branch name".** The title produced nothing usable after slugification — typically a title made only of punctuation or non-Latin script. Use a template without `{slug}`, or rename the ticket.

**Status didn't change.** Three common causes: your tracker has no in-progress concept (plain GitHub and GitLab issues are open/closed only), the workflow forbids the transition from the current status, or `inProgressStatus` names a status that doesn't exist in that list. The branch still gets created either way — a failed status write isn't a failed task.

**Python not found.** Install Python 3, or ask the skill to build the name without the script. You'll lose the guarantee that the same ticket always yields the same branch name.

## Updating and uninstalling

Installed as a plugin:

```
/plugin update ticket-branch@afifkraiem-plugins
/plugin uninstall ticket-branch@afifkraiem-plugins
```

Installed by copy, update by replacing the skill directory:

```bash
rm -rf .claude/skills/ticket-branch
cp -r path/to/ticket-branch/skills/ticket-branch .claude/skills/
```

Your `.ticket-branch.json` is separate and survives updates.

Uninstall by deleting the directory, and `.claude/commands/branch.md` if you installed it. To also drop the tracker connection:

```bash
claude mcp remove clickup
```

Run the script's tests after any change to it:

```bash
python3 skills/ticket-branch/scripts/test_branch_name.py
```
