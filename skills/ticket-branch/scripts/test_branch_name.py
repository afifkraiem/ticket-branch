#!/usr/bin/env python3
"""Regression tests for branch_name.py. Run: python3 scripts/test_branch_name.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from branch_name import build, slugify, validate_ref  # noqa: E402

PASS = FAIL = 0


def eq(got, want, label):
    global PASS, FAIL
    if got == want:
        PASS += 1
        print(f"  ok    {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}\n          want {want!r}\n          got  {want.__class__.__name__} {got!r}")


def name(**kw):
    kw.setdefault("template", "{type}/{id}-{slug}")
    return build(**kw)["branch"]


print("slug + naming")
eq(name(ticket_id="PROJ-123", title="[BUG] Le résumé PDF plante à l'export", ticket_type="fix"),
   "fix/PROJ-123-le-resume-pdf-plante-a-l-export", "accents + [BUG] prefix")
eq(name(ticket_id="ABC-42", title="ABC-42: Ajouter l'export CSV", ticket_type="feature"),
   "feature/ABC-42-ajouter-l-export-csv", "id already in title is not repeated")
eq(name(ticket_id="X-3", title="[Front][URGENT] TODO: corriger le header", ticket_type="fix"),
   "fix/X-3-corriger-le-header", "stacked noise prefixes")
eq(name(ticket_id="X-1", title="", ticket_type="fix", allow_empty_slug=True),
   "fix/X-1", "empty title leaves no dangling separator when explicitly allowed")
eq(name(ticket_id="PROJ-7", title="🚀 Déployer sur staging", ticket_type="chore", id_case="lower"),
   "chore/proj-7-deployer-sur-staging", "emoji dropped, id lowercased")
eq(name(ticket_id="prj-9", title="Fix flaky e2e tests", ticket_type="test", template="{type}/{slug}"),
   "test/fix-flaky-e2e-tests", "template without id")
eq(name(ticket_id="A-1", title="Add login", ticket_type="feat",
        template="{user}/{type}/{id}-{slug}", extra={"user": "alice"}),
   "alice/feat/A-1-add-login", "extra placeholder")

print("truncation")
eq(name(ticket_id="86abc1234", ticket_type="chore",
        title="Refactoriser complètement la couche de persistance des utilisateurs et des rôles"),
   "chore/86abc1234-refactoriser-completement-la-couche-de", "cuts on a word boundary")
eq(slugify("Corriger le bandeau de consentement RGPD", max_length=12),
   "corriger-le", "small max length still ends on a boundary")
eq(slugify("Corriger le bandeau de consentement RGPD sur toutes les pages", max_length=0),
   "corriger-le-bandeau-de-consentement-rgpd-sur-toutes-les-pages", "0 means unlimited")

print("hostile input")
eq(name(ticket_id="X-1", title='oops; rm -rf / && echo ../../~^:?*[hi] "quoted"', ticket_type="fix"),
   "fix/X-1-oops-rm-rf-echo-hi-quoted", "shell metachars and .. are stripped")
eq(validate_ref("feature/a..b"), ["contains '..'"], "'..' rejected")
eq("ends with '.' or '.lock'" in validate_ref("fix/x.lock"), True, "'.lock' suffix rejected")
eq(validate_ref("fix/-x") == [], True, "internal leading dash in a segment is allowed by git")
eq(bool(validate_ref("fix/ x")), True, "space rejected")
eq(name(ticket_id="X-2", title="Update yarn lock", ticket_type="chore", template="{slug}"),
   "update-yarn-lock", "'lock' without a dot is fine")

print("failure modes")
for label, kw in [
    ("empty title with {slug} in template is refused", dict(ticket_id="X-1", title="", ticket_type="fix")),
    ("title reducing to the id alone is refused", dict(ticket_id="NEX-1234", title="NEX-1234", ticket_type="feature")),
]:
    try:
        build(**kw)
        eq("no raise", "ValueError", label)
    except ValueError as exc:
        eq("description" in exc.args[0], True, label)
eq(name(ticket_id="X-1", title="", ticket_type="fix", template="{type}/{id}"),
   "fix/X-1", "template without {slug} needs no title")
try:
    build(ticket_id="A-1", title="hi", ticket_type="fix", template="{type}/{author}")
    eq("no raise", "KeyError", "unknown placeholder raises")
except KeyError as exc:
    eq("{author}" in exc.args[0], True, "unknown placeholder raises with a useful message")
eq(bool(validate_ref(build(ticket_id="", title="!!!", ticket_type="", allow_empty_slug=True)["branch"])), True,
   "empty result is invalid")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
