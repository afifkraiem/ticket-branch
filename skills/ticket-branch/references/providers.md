# Provider reference

Per-tracker guidance for step 3 (fetch) and step 4 (normalize) of the skill.

## Contents

- [How to read this file](#how-to-read-this-file)
- [Identifying the provider](#identifying-the-provider)
- [Jira](#jira) · [Linear](#linear) · [ClickUp](#clickup) · [GitHub Issues](#github-issues) · [GitLab Issues](#gitlab-issues) · [Asana](#asana) · [Shortcut](#shortcut) · [Notion](#notion) · [Azure DevOps](#azure-devops) · [YouTrack](#youtrack) · [Monday](#monday) · [Trello](#trello)
- [Unlisted trackers](#unlisted-trackers)
- [CLI fallbacks](#cli-fallbacks)

## How to read this file

Tool names below are the patterns most MCP servers for each tracker use, but they are **not** a contract. Server names are chosen by whoever configured the connection, and tool names differ between the official server and community implementations. Always match against the tool list you actually have, and prefer a tool's own description over the name when they disagree.

The useful, stable part of this file is the second half of each entry: ID formats, where the issue type lives, and how statuses work. Those are properties of the tracker, not of the MCP server.

## Identifying the provider

By URL hostname, which is the most reliable signal:

| Hostname | Provider |
|---|---|
| `*.atlassian.net`, self-hosted Jira | jira |
| `linear.app` | linear |
| `app.clickup.com` | clickup |
| `github.com` | github |
| `gitlab.com`, self-hosted GitLab | gitlab |
| `app.asana.com` | asana |
| `app.shortcut.com` | shortcut |
| `notion.so`, `*.notion.site` | notion |
| `dev.azure.com`, `*.visualstudio.com` | azure-devops |
| `*.youtrack.cloud` | youtrack |
| `*.monday.com` | monday |
| `trello.com` | trello |

By ID shape, when there's no URL:

| Shape | Candidates |
|---|---|
| `ABC-123` | jira, linear, shortcut, youtrack — **ambiguous** |
| `#123` or bare `123` | github, gitlab (needs repo context) |
| `owner/repo#123` | github, gitlab |
| 7-9 char lowercase alphanumeric, e.g. `86abc1234` | clickup |
| 16+ digit numeric | asana, monday |
| UUID or 32-hex | notion |

Ambiguity between `ABC-123` trackers only matters if several are connected. With one, use it. With several, ask — the prefix belongs to a project or team key the user knows and you don't.

## Jira

Look for servers named `jira` or `atlassian`. Typical tools: `getJiraIssue` / `get_issue`, `transitionJiraIssue`, `editJiraIssue`, and a JQL search tool.

- **ID**: `PROJECT-123`, case-insensitive on input, uppercase in practice.
- **Type**: native and required — `fields.issuetype.name` (`Bug`, `Story`, `Task`, `Epic`, `Sub-task`, plus whatever the admin added).
- **Status**: Jira does not accept a status name on write. You must read the available **transitions** for that issue and post a transition ID. Fetch transitions before attempting the move, and map your chosen status name to its transition. A status can be unreachable from the current one if the workflow forbids it — report that rather than retrying.
- **Labels**: `fields.labels`, a flat string array. Components (`fields.components`) are separate and sometimes carry type-ish meaning.
- Self-hosted instances lag Cloud on API shape; if a field is missing, fall back to the cascade in step 5 rather than failing.

## Linear

Servers named `linear`. Typical tools: `get_issue`, `update_issue`, `list_issue_statuses`, `list_teams`.

- **ID**: `TEAM-123`. The API also has an internal UUID; accept either, and keep the `TEAM-123` form as `displayId` since that's what people paste.
- **Type**: no native type field. Type comes from labels — Linear teams conventionally use `Bug`, `Feature`, `Improvement`, `Chore`.
- **Status**: workflow states are per-team, with a `type` category (`backlog`, `unstarted`, `started`, `completed`, `canceled`). Prefer the state whose category is `started` — a semantic match rather than a name match, so it survives a team renaming "In Progress" to "Building". Teams routinely have **several** `started` states (`Building` and `In Review` both qualify), so break the tie on the lowest `position`, which is the earliest column on the board. Only ask if positions are missing or equal; asking whenever two states share a category would fire on most real Linear setups.
- Linear also exposes a suggested branch name per issue (`branchName`). If the repo has no config, that's a reasonable default; if the repo has a config, the team's template wins.

## ClickUp

Servers named `clickup`. Typical tools: `getTask`, `updateTask`, `getListStatuses`.

- **ID**: internal IDs are short lowercase alphanumeric (`86abc1234`). Custom IDs (`ABC-123`) are an optional per-workspace feature and need a flag on the fetch call to resolve — check the tool's parameters for something like `custom_task_ids`, which usually also requires a team/workspace ID.
- **Type**: custom task types exist but are often unused. Check `custom_item_id`, then tags, then title.
- **Status**: per-list, free-text, lowercase in the API. Read the list's statuses; do not assume `in progress` exists.
- **Display ID**: prefer the custom ID when present, since that's what appears in the team's conversations.

## GitHub Issues

Servers named `github`. Typical tools: `get_issue`, `update_issue`, `add_issue_comment`.

- **ID**: issue number, needing `owner` and `repo` for context. Derive those from the git remote when the user gave a bare `#123` — that's almost always what they mean.
- **Type**: labels only (`bug`, `enhancement`, `documentation`). Newer repos may have native issue types; use them if present.
- **Status**: issues are open/closed, with no in-progress state. If the repo uses GitHub Projects, moving the item's Status field is the equivalent — that's a separate API surface and often not exposed by the MCP server. When there's no way to express in-progress, say so and skip step 8; don't close the issue as a substitute.
- Assigning the issue to the user is the closest available signal that work has started.

## GitLab Issues

Servers named `gitlab`. Typical tools: `get_issue`, `update_issue`.

- **ID**: issue IID (project-scoped, so `#42` differs per project) plus a project ID or path.
- **Type**: native `issue_type` (`issue`, `incident`, `test_case`, `task`) is coarse; labels carry the real meaning. GitLab's scoped labels (`type::bug`, `workflow::in-progress`) are common and worth checking first — the `type::` prefix is a strong signal.
- **Status**: open/closed, same limitation as GitHub. Teams express progress with a scoped label like `workflow::in progress`, which is settable. Prefer that when a `workflow::` or `status::` scoped label exists.

## Asana

Servers named `asana`. Typical tools: `get_task`, `update_task`, `get_project_sections`.

- **ID**: long numeric GID.
- **Type**: no native type; custom fields or tags.
- **Status**: progress is a **section** within a project, or a custom field — not a status property. Moving to in-progress usually means moving the task to a section. Read the project's sections and match on name.
- `displayId` is awkward here: the GID is long and meaningless in a branch name. Prefer a short custom field if the team has one, otherwise consider a template without `{id}`.

## Shortcut

Servers named `shortcut`. Typical tools: `get_story`, `update_story`, `get_workflows`.

- **ID**: `sc-123` or bare numeric.
- **Type**: native `story_type` — exactly `feature`, `bug`, or `chore`, which maps onto the default type map with no translation.
- **Status**: workflow states per workflow, each with a `type` category similar to Linear (`unstarted`, `started`, `done`). Match on the `started` category, and where several qualify, take the lowest `position` as with Linear.
- Shortcut also suggests a branch name; same rule as Linear — config wins if present.

## Notion

Servers named `notion`. Typical tools: `retrieve_page`, `update_page`, `query_database`.

- **ID**: UUID, or 32 hex characters without dashes.
- **Type**: a select or multi-select property whose name varies (`Type`, `Category`, `Kind`). Inspect the database schema rather than guessing property names.
- **Status**: a `status` or `select` property, values entirely team-defined. Read the property's options.
- Titles are rich text; extract plain text before slugifying.
- Notion pages have no short human ID, so `{id}` in a template produces an unreadable branch. Suggest a template without it.

## Azure DevOps

Servers named `azure-devops` or `ado`. Typical tools: `get_work_item`, `update_work_item`.

- **ID**: numeric work item ID, unique across the org.
- **Type**: native `System.WorkItemType` (`Bug`, `User Story`, `Task`, `Feature`, `Epic`), which depends on the process template — Agile, Scrum and CMMI use different names, so match loosely.
- **Status**: `System.State`, valid values depend on the type. `Active`, `Doing`, or `In Progress` per template.

## YouTrack

Servers named `youtrack`. Typical tools: `get_issue`, `apply_command`.

- **ID**: `PROJ-123`.
- **Type**: a `Type` custom field.
- **Status**: a `State` custom field. YouTrack's command API is the idiomatic way to change it (a command string like `State In Progress`), which is worth preferring when exposed since it handles the field plumbing.

## Monday

Servers named `monday`. Typical tools: `get_item`, `change_column_value`.

- **ID**: numeric item ID plus a board ID.
- **Type**: a status-type column, board-specific.
- **Status**: also a status-type column, often literally named `Status`. Read the board's column definitions — labels are indexed and colour-coded, and writes may need the index rather than the text.

## Trello

Servers named `trello`. Typical tools: `get_card`, `update_card`, `get_lists`.

- **ID**: card ID (24-hex) or short link.
- **Type**: labels.
- **Status**: the list the card sits in. Moving to in-progress means moving the card to another list — read the board's lists and match on name.

## Unlisted trackers

An unlisted tracker with an MCP server is usually still workable. Read the tool descriptions to find a fetch-by-id tool and an update tool, map the response onto the normalized shape, and follow the generic path. Two questions decide most of it:

1. Where does type live — a native field, labels, or nowhere?
2. Is in-progress a status field, a category on a workflow state, a section, or a list?

Trackers cluster into a handful of models on both counts, and the entries above cover all of them. If the mapping works, offer to add a short entry to this file — that's the intended way for the skill to grow.

## CLI fallbacks

When no tracker MCP is connected, these give a usable path for git-hosted issues:

```bash
gh issue view 123 --json number,title,labels,state,url        # GitHub
glab issue view 123 --output json                              # GitLab
```

Check the CLI exists and is authenticated (`gh auth status`) before relying on it. There's no CLI equivalent for the other trackers, so for those, ask the user for the ticket title and note in the report that the ticket status wasn't touched.
