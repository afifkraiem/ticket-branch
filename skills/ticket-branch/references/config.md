# Config reference

The config file pins a team's conventions so every branch comes out the same regardless of who ran the command. It lives at `.ticket-branch.json` in the repo root, or `.claude/ticket-branch.json`. Commit it.

Every key is optional. A missing key falls back to the default below, so a config holding only `baseBranch` is perfectly valid — write the smallest config that captures what the team actually cares about, since every key added is a key someone has to maintain.

## Schema

| Key | Type | Default | Meaning |
|---|---|---|---|
| `baseBranch` | string | `develop` if it exists, else the remote's default branch | Branch to cut from |
| `remote` | string | `origin` | Remote to fetch from |
| `branchTemplate` | string | `{type}/{id}-{slug}` | Name template; see placeholders below |
| `slugMaxLength` | number | `50` | Max slug length, truncated on a word boundary |
| `typeMap` | object | see below | Prefix → matching keywords |
| `defaultType` | string | `feature` | Prefix when nothing matches |
| `idSource` | `"customId"` \| `"internalId"` | `customId` | Which ID to use for `{id}`, when the tracker has both |
| `idCase` | `"preserve"` \| `"upper"` \| `"lower"` | `preserve` | Case applied to `{id}` |
| `inProgressStatus` | string \| null | `null` (infer) | Exact target status name |
| `assignSelf` | boolean | `false` | Assign the ticket to the current user |
| `push` | boolean | `false` | Push the branch with upstream tracking after creating it |
| `provider` | string \| null | `null` (detect) | Force a tracker when several MCPs are connected |
| `commentOnTicket` | boolean | `false` | Post a comment naming the branch |

## Template placeholders

`{type}` the derived prefix · `{id}` the ticket ID per `idSource` and `idCase` · `{slug}` the slugified title.

Common variants:

| Template | Result |
|---|---|
| `{type}/{id}-{slug}` | `fix/PROJ-123-pdf-export-crashes` |
| `{id}-{slug}` | `PROJ-123-pdf-export-crashes` |
| `{type}/{id}` | `fix/PROJ-123` |
| `{type}/{slug}` | `fix/pdf-export-crashes` |
| `{id}/{slug}` | `PROJ-123/pdf-export-crashes` |

Two things worth knowing before designing a template. A slash makes the segment before it a directory in git's ref storage, so a repo can't have both a branch `feature` and a branch `feature/x` — harmless with a consistent template, confusing when mixing. And templates omitting `{id}` lose the traceability that motivates this whole workflow, so they only really suit trackers with unusable IDs, like Notion or Asana.

## Type map

Keys are branch prefixes, values are keywords matched case-insensitively against the ticket's native type, then its labels, then words in its title. First match wins, so order the keys from most to least specific.

Default:

```json
{
  "fix": ["bug", "bogue", "anomalie", "hotfix", "incident", "regression", "défaut", "defect"],
  "feature": ["feature", "fonctionnalité", "story", "user story", "us", "enhancement", "improvement", "evolution", "évolution", "epic"],
  "chore": ["chore", "tech", "technique", "refactor", "refacto", "refactoring", "dette", "debt", "ci", "build", "deps", "dependencies", "docs", "documentation", "test", "config"]
}
```

Providing `typeMap` **replaces** the default rather than merging with it, which keeps the file honest — you can read the config and know exactly what will match. Copy the default and edit if you only want to add a keyword.

For Conventional Commits alignment, a fuller map:

```json
{
  "typeMap": {
    "fix": ["bug", "hotfix", "incident", "regression"],
    "perf": ["performance", "perf", "optimization", "slow"],
    "docs": ["docs", "documentation", "readme"],
    "test": ["test", "tests", "coverage", "e2e"],
    "build": ["build", "ci", "pipeline", "deps", "dependencies"],
    "refactor": ["refactor", "refacto", "cleanup", "tech debt"],
    "feat": ["feature", "story", "enhancement", "epic"]
  },
  "defaultType": "feat"
}
```

## Examples

Jira team on `develop`, uppercase keys, explicit status:

```json
{
  "baseBranch": "develop",
  "branchTemplate": "{type}/{id}-{slug}",
  "idCase": "upper",
  "inProgressStatus": "In Progress",
  "assignSelf": true
}
```

Linear team on trunk, no type prefix, pushing immediately:

```json
{
  "baseBranch": "main",
  "branchTemplate": "{id}-{slug}",
  "slugMaxLength": 40,
  "push": true
}
```

Notion-based tracker with unusable IDs:

```json
{
  "provider": "notion",
  "branchTemplate": "{type}/{slug}",
  "slugMaxLength": 60
}
```

Two trackers connected, ClickUp is the one that counts:

```json
{
  "provider": "clickup",
  "idSource": "customId",
  "baseBranch": "develop"
}
```

## Writing a config for a team

Infer before asking. `git for-each-ref --sort=-committerdate --count=50 --format='%(refname:short)' refs/remotes` shows what the team already does, and most teams have a consistent de facto pattern nobody has written down. Propose a config matching it, show a sample branch name it would produce, and let the user correct it. Handing someone a config derived from their own history gets agreement far faster than a questionnaire.
