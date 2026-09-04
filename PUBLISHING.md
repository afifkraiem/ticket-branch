# Publishing

This repo is both a **plugin marketplace** and the plugin itself, so users install it in two commands. Everything below assumes you've pushed it to a public git host.

- [Before you publish](#before-you-publish)
- [Route 1 — plugin marketplace (recommended)](#route-1--plugin-marketplace-recommended)
- [Route 2 — copy the files](#route-2--copy-the-files)
- [Route 3 — a .skill bundle for claude.ai](#route-3--a-skill-bundle-for-claudeai)
- [Route 4 — inside one organization](#route-4--inside-one-organization)
- [Releasing a new version](#releasing-a-new-version)
- [Getting it found](#getting-it-found)
- [Renaming or removing](#renaming-or-removing)

## Before you publish

This repo is already configured for `github.com/afifkraiem/ticket-branch`, with the marketplace named `afifkraiem-plugins`. If you fork it, change the identity in three files first, so nothing publishes under someone else's name: the marketplace `name`, `owner`, `homepage` and `repository` in `.claude-plugin/marketplace.json`; `author`, `homepage` and `repository` in `.claude-plugin/plugin.json`; and the copyright holder in `LICENSE`.

Name the **marketplace** after yourself or your org (`afifkraiem-plugins`), not after the plugin. Users can register only one marketplace per name, so a second marketplace called `ticket-branch` would silently replace yours in their setup. The plugin keeps the short name, giving `/plugin install ticket-branch@afifkraiem-plugins`.

Some marketplace names are reserved for Anthropic (`claude-plugins-official`, `agent-skills`, `anthropic-plugins` and others), along with names that imitate them. A marketplace using one stops loading for everyone who added it, so steer well clear.

Then validate and test locally before pushing:

```bash
claude plugin validate .
```

```
/plugin marketplace add ./path/to/ticket-branch
/plugin install ticket-branch@afifkraiem-plugins
```

Install from a local path first. It catches manifest mistakes in seconds, whereas a broken push means everyone who added your marketplace sees the failure.

## Route 1 — plugin marketplace (recommended)

Push to a public repo. Users then run:

```
/plugin marketplace add afifkraiem/ticket-branch
/plugin install ticket-branch@afifkraiem-plugins
```

This is the route worth putting in your README. It gives them version tracking, `/plugin update`, and background auto-updates, none of which a file copy provides.

Two consequences of plugin installation to document for your users:

**Skills and commands get namespaced under the plugin name.** The `/branch` command becomes `/ticket-branch:branch`. The skill still triggers on plain language the same way, so this only affects people who reach for the slash command.

**Plugins are copied into a cache, not used in place.** Nothing in the plugin may reference files outside its own directory — no `../shared`. This repo is self-contained, so it's only a constraint to remember if you later split it up.

Non-GitHub hosts work with the full URL:

```
/plugin marketplace add https://gitlab.com/afifkraiem/ticket-branch.git
```

## Route 2 — copy the files

Keep the copy instructions in your README as a fallback. They're the only route for someone who wants to vendor the skill into their own repo's `.claude/skills/`, or who is on a Claude Code version older than the plugin system. See [GUIDE.md](GUIDE.md).

## Route 3 — a .skill bundle for claude.ai

Skills also run in claude.ai and the desktop app, which take a zipped skill folder rather than a plugin repo. Build one from the skill directory:

```bash
cd skills && zip -r ../ticket-branch.skill ticket-branch -x '*__pycache__*'
```

Attach it to your GitHub releases so those users have something to download. Worth being upfront in the README that the git steps assume a local repository, so the skill is far less useful outside a terminal — the branch creation is the whole point.

## Route 4 — inside one organization

For a company rollout rather than public release, two mechanisms beat asking people to run install commands.

Commit a marketplace declaration to the repos where you want it. Teammates get it once they trust the folder, with no separate prompt — put this in `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "afifkraiem-plugins": {
      "source": { "source": "github", "repo": "afifkraiem/ticket-branch" }
    }
  },
  "enabledPlugins": {
    "ticket-branch@afifkraiem-plugins": true
  }
}
```

Or distribute through **Organization settings > Plugins** on a Team or Enterprise plan, which syncs a private marketplace repo to everyone in the org. That route requires the marketplace repo to be private or internal, and each plugin source to be a `github`, `url`, `git-subdir`, or `./` relative path.

## Releasing a new version

`version` in `plugin.json` is the update signal. Users stay on their cached copy until that string changes, so pushing commits without bumping it ships nothing:

```bash
# edit version in .claude-plugin/plugin.json
git commit -am "release 0.2.0" && git tag v0.2.0 && git push --tags
```

Don't also set `version` in the marketplace entry — `plugin.json` silently wins, and a stale manifest there will mask it. Alternatively, omit `version` from both and Claude Code uses the resolved commit SHA, so every push is an update. That suits a plugin under active development; a declared version suits one with users who'd rather not be surprised.

Run the script tests before tagging:

```bash
python3 skills/ticket-branch/scripts/test_branch_name.py
```

Users pick up marketplace changes with `/plugin marketplace update`, or automatically in the background.

## Getting it found

There's no central index to submit to that guarantees placement. What actually drives adoption:

- **GitHub topics** — `claude-code`, `claude-plugin`, `claude-skill`, `mcp`. This is how most people browsing find plugins.
- **A README that shows output.** The value here is legible in three lines of terminal output; lead with it.
- **The tracker list.** People search for their tracker, not for "branch naming". Name Jira, Linear and ClickUp in the description and topics.
- **Community lists.** Several `awesome-claude-code` style repos accept PRs.
- **Anthropic's official directory** (`anthropics/claude-plugins-official`) is Anthropic-managed rather than open submission; check that repo for whatever current guidance it publishes.

## Renaming or removing

A plugin's `name` is its stable identifier — users reference it in their settings, so changing it breaks every install. To change only the displayed label, set `displayName` and leave `name` alone.

If you must rename, add a top-level `renames` map to `marketplace.json` so existing users migrate instead of hitting `plugin-not-found`:

```json
{
  "renames": { "old-name": "ticket-branch" }
}
```

Treat that map as append-only history: keep old entries even long after you think everyone has migrated, and add a second entry rather than editing the first if you rename again.
