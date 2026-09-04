#!/usr/bin/env python3
"""Build a deterministic git branch name from a ticket id and title.

Kept as a script rather than done inline so the same ticket always yields the
same branch name, whoever runs it and however many times.

Usage:
    python3 branch_name.py --id PROJ-123 --title "[BUG] Export PDF crashes" --type fix
    python3 branch_name.py --id 42 --title "Ajouter le résumé" --type feature \
        --template "{type}/{id}-{slug}" --max-slug-length 40 --json

Exits 1 with a message on stderr if the result is not a valid git ref.
Python 3.8+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

DEFAULT_TEMPLATE = "{type}/{id}-{slug}"
DEFAULT_MAX_SLUG = 50

# Bracketed or colon-terminated prefixes trackers and humans leave in titles.
NOISE_PREFIX = re.compile(
    r"""^\s*(?:
          \[[^\]]{0,40}\]            # [BUG], [WIP], [Front]
        | \([^)]{0,40}\)             # (bug), (urgent)
        | (?:todo|fixme|wip|bug|fix|feat|feature|chore|hotfix|task|story)\s*:
    )\s*""",
    re.IGNORECASE | re.VERBOSE,
)

# Git ref rules we can violate through a template or a hostile title.
# See git-check-ref-format(1).
FORBIDDEN_SUBSTRINGS = ("..", "@{", "//", "\\")
FORBIDDEN_CHARS = set(' \t\n\r~^:?*[]"\'`$;&|<>()!#%{},')


def strip_accents(text: str) -> str:
    """Transliterate to ASCII: 'résumé' -> 'resume'."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def slugify(title: str, max_length: int = DEFAULT_MAX_SLUG, drop: str = "") -> str:
    """Turn a ticket title into a lowercase hyphenated slug.

    `drop` is removed from the title when present, so an id already inside the
    title doesn't get repeated in the branch name.
    """
    text = title or ""

    # Strip noise prefixes repeatedly: "[BUG] TODO: x" has two.
    while True:
        stripped = NOISE_PREFIX.sub("", text, count=1)
        if stripped == text:
            break
        text = stripped

    text = strip_accents(text).lower()

    if drop:
        text = re.sub(re.escape(strip_accents(drop).lower()), " ", text)

    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text)

    if max_length > 0 and len(text) > max_length:
        cut = text[:max_length]
        # Prefer a word boundary, unless that leaves almost nothing.
        boundary = cut.rfind("-")
        if boundary >= max_length // 2:
            cut = cut[:boundary]
        text = cut.strip("-")

    return text


def format_id(raw_id: str, case: str = "preserve") -> str:
    """Sanitize a ticket id for use in a ref, without mangling its shape."""
    value = strip_accents(raw_id or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    if case == "upper":
        value = value.upper()
    elif case == "lower":
        value = value.lower()
    return value


def validate_ref(name: str) -> list[str]:
    """Return a list of reasons `name` is not a usable branch name."""
    problems: list[str] = []

    if not name:
        problems.append("name is empty")
        return problems

    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in name:
            problems.append(f"contains {bad!r}")

    offenders = sorted({c for c in name if c in FORBIDDEN_CHARS or ord(c) < 0x20})
    if offenders:
        problems.append("contains forbidden characters: " + " ".join(repr(c) for c in offenders))

    if name.startswith("/") or name.endswith("/"):
        problems.append("starts or ends with '/'")
    if name.startswith("-"):
        problems.append("starts with '-'")
    if name.endswith(".") or name.endswith(".lock"):
        problems.append("ends with '.' or '.lock'")
    if any(seg.startswith(".") or seg.endswith(".lock") or not seg for seg in name.split("/")):
        problems.append("has an empty segment, or a segment starting with '.' or ending in '.lock'")
    if name == "@":
        problems.append("is '@'")

    return problems


def build(
    ticket_id: str,
    title: str,
    ticket_type: str,
    template: str = DEFAULT_TEMPLATE,
    max_slug_length: int = DEFAULT_MAX_SLUG,
    id_case: str = "preserve",
    extra: dict[str, str] | None = None,
    allow_empty_slug: bool = False,
) -> dict:
    formatted_id = format_id(ticket_id, id_case)
    slug = slugify(title, max_slug_length, drop=formatted_id)

    values = {
        "type": format_id(ticket_type, "lower"),
        "id": formatted_id,
        "slug": slug,
    }
    values.update(extra or {})

    used = set(re.findall(r"\{(\w+)\}", template))

    if "slug" in used and not slug and not allow_empty_slug:
        raise ValueError(
            "slug is empty: the title is missing, or reduces to nothing once the id "
            "and noise prefixes are stripped. Pass a title derived from the ticket "
            "description, or --allow-empty-slug to build an id-only name."
        )

    unknown = used - values.keys()
    if unknown:
        raise KeyError(
            "unknown placeholder(s) in template: "
            + ", ".join(sorted(f"{{{k}}}" for k in unknown))
            + ". Available: "
            + ", ".join(sorted(f"{{{k}}}" for k in values))
        )

    name = template.format(**values)
    # An empty placeholder can leave a dangling separator, e.g. "fix/PROJ-123-".
    name = re.sub(r"[-/]{2,}", lambda m: m.group(0)[0], name).strip("-/")

    return {"branch": name, **values, "template": template}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a git branch name from a ticket.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--id", default="", help="ticket id, e.g. PROJ-123")
    parser.add_argument("--title", default="", help="ticket title")
    parser.add_argument("--type", default="", help="branch type prefix, e.g. fix")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE)
    parser.add_argument("--max-slug-length", type=int, default=DEFAULT_MAX_SLUG)
    parser.add_argument("--id-case", choices=["preserve", "upper", "lower"], default="preserve")
    parser.add_argument(
        "--allow-empty-slug",
        action="store_true",
        help="accept an id-only name when the title slugifies to nothing",
    )
    parser.add_argument(
        "--var",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra template placeholder; repeatable",
    )
    parser.add_argument("--json", action="store_true", help="print components as JSON")
    args = parser.parse_args(argv)

    extra: dict[str, str] = {}
    for item in args.var:
        key, _, value = item.partition("=")
        if not key or not _:
            print(f"error: --var expects KEY=VALUE, got {item!r}", file=sys.stderr)
            return 2
        extra[key] = format_id(value, "preserve")

    try:
        result = build(
            ticket_id=args.id,
            title=args.title,
            ticket_type=args.type,
            template=args.template,
            max_slug_length=args.max_slug_length,
            id_case=args.id_case,
            extra=extra,
            allow_empty_slug=args.allow_empty_slug,
        )
    except (KeyError, ValueError) as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 2

    problems = validate_ref(result["branch"])
    if problems:
        print(
            f"error: {result['branch']!r} is not a valid branch name: "
            + "; ".join(problems),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else result["branch"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
