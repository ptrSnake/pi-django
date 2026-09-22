# Plan: English project + docs reorganization + local usage

## Context

The `pi-django` package repo currently mixes Italian and English:

- `README.md` (package) — Italian
- `templates/common/README.md` (generated project README) — Italian
- `PLAN.md` (planning artifact) — Italian
- `STILE-DJANGO.md` (1732-line Django styleguide that the scaffold implements) — Italian
- The generated code is already English (the guide mandates it), but code comments /
  docstrings reference the Italian filename `STILE-DJANGO.md` in ~25 places
  (`extensions/index.ts` ×4, template `.py` docstrings ×20, `pyproject.toml` description,
  generated README).

The user wants the project to be in English (translate the markdown files), a decision on
where `PLAN.md` and `STILE-DJANGO.md` should live (a different folder, name TBD), and
instructions on how to use the package locally.

## Decisions (confirmed by user)

1. **STILE-DJANGO.md** — translate the full 1732-line styleguide to English
2. **Destination folder** — `docs/`
   - `STILE-DJANGO.md` → `docs/django-styleguide.md` (translated + renamed)
   - `PLAN.md` → `docs/plans/PLAN.md` (kept as history, translated)
3. **Rename + reference updates** — update all code references from `STILE-DJANGO.md §x`
   to `Django Styleguide §x` (keep section numbers)

## Approach (pending decisions)

### 1. Folder reorganization

```
pi-django/
├── README.md                    # package docs (English)
├── extensions/
├── templates/
├── docs/
│   ├── django-styleguide.md     # translated from STILE-DJANGO.md (English)
│   └── plans/PLAN.md            # translated plan, kept as history
└── test/
```

### 2. English translations

- `README.md` — full English rewrite (title, install from npm/git, usage of the tool and
  `/django-scaffold` command, generated structure, verification); add a **"Local usage"**
  section answering "how do I use this locally".
- `templates/common/README.md` — English rewrite (quickstart, dev, structure), references
  updated to the new guide name.
- `PLAN.md` — translate if kept.
- `STILE-DJANGO.md` — translate if approved (large mechanical task, keep § numbers so code
  references remain valid).

### 3. Reference updates (non-md files)

Where the code mentions `STILE-DJANGO.md`:
- `extensions/index.ts` — header comment, tool summary, tool description, command
  description (4 places): use "Django Styleguide (HackSoft)" or the new doc name.
- `templates/common/pyproject.toml` — description field.
- `templates/**/*.py` docstrings — `(STILE-DJANGO.md §N)` → `(Django Styleguide §N)` or new
  filename.
- `templates/common/README.md` — same.

Keep the `§` section numbers so cross-references survive a translation.

## Files to modify

- `README.md` (rewrite, English + Local usage)
- `templates/common/README.md` (rewrite, English)
- `PLAN.md` → move/translate/delete (pending decision)
- `STILE-DJANGO.md` → move/translate/rename (pending decision)
- `extensions/index.ts` (reference strings)
- `templates/common/pyproject.toml` (description)
- ~20 template `.py` docstrings (reference strings)
- `.gitignore` unchanged — `docs/` is committed

## Reuse

- Existing section headers of STILE-DJANGO.md (anchor `§` numbers) — keep stable.
- No new code logic; pure string/documentation changes.

## Steps

- [x] Confirm decisions (guide translation, folder name, PLAN.md fate, rename)
- [x] Create `docs/` (and `docs/plans/` if kept) and move files
- [ ] Translate `/ rewrite` the md files in place
- [ ] Update code references (`extensions/index.ts`, pyproject description, py docstrings)
- [ ] Re-verify: extension loads (`pi -e`), ruff/pytest still green on a fresh scaffold
- [ ] Commit (message mentions docs reorganization)

## Verification

- `node --experimental-strip-types test/load-test.ts` — extension loads, 3 frameworks OK
- One real scaffold (`pi -e … −p …`) → `uv run ruff check . && uv run pytest` green
- `grep -ri "stile" .` (repo, excluding .git/node_modules) returns nothing
- `README.md` reads against the new `docs/` layout; markdown links resolve