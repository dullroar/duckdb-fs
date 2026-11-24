# Agent contract

`duckdb-fs` is a read-only FUSE projection of Great Expectations extractor facts.
It uses DuckDB to query the progressive set intersection specified by a path.

## Standing rules

- Work on a branch. Never commit directly to `main`.
- Do not write credentials, personal data, personal paths, private host names or
  sensitive record-level examples. Use placeholders and aggregate evidence.
- Do not push, publish, force-push or add a remote without user authorization.
- Write in Simplified Technical English.
- User instructions take precedence. When sources conflict, use this order:
  user instructions, this file, `docs/design/`, the named plan, domain documentation
  and references, `memory/`, implementation and tests, historical notes.
- Do not weaken the controls. You may run the local checks at any time. CI runs
  them in all cases. Do not change or disable the controls, the pin
  (`scripts/controls-requirements.txt`), `controls.toml` or the workflows to make
  an unrelated task pass. The driver checks the gate and `touches` of each step.
  A change to the gate or a file outside `touches` fails the step. Send each piece
  of work to the cheapest executor that can do it, and let the gate decide if the
  work is done. The full policy is at
  <https://github.com/dullroar/ralph-looper/blob/main/docs/routing.md>.
- Before changing this repository's structure, read
  [repo-template](https://github.com/dullroar/repo-template) and
  [ralph-looper](https://github.com/dullroar/ralph-looper). Account for their layout,
  plan format, generated indexes, worktree rules, and validation commands in the change.

## Load context in this order

1. Read this file.
2. Read the short indexes in full: [README.md](./README.md), [docs/README.md](./docs/README.md),
   [memory/AGENTS.md](./memory/AGENTS.md), [plans/AGENTS.md](./plans/AGENTS.md),
   and [scripts/AGENTS.md](./scripts/AGENTS.md).
3. Open only the entries that match the task. For a large file, search its headings
   and read the relevant ranges.
4. Stop when you know the decision, intended files, constraints and validation method.

## Context ownership

- Put universal rules here.
- Put architectural reasons in `docs/design/`. Use one premise per file.
- Put findings that cost time to discover in `memory/`. Use one file per topic.
  Record the date, observation and conditions. Note when the finding may be
  obsolete. Edit the existing topic when a finding changes. Keep raw logs out.
- Put execution state in `plans/` and deterministic automation in `scripts/`.
  Reuse existing scripts before adding new ones.
- Start each routed Markdown file with `gist: "Read me when: ..."` front matter.
  Start each script with a `Run me when:` line in the first 25 lines.
- Keep each fact in its canonical source.

Edit the documentation index by hand. Run `python3 scripts/build_indexes.py` to
update the generated indexes, including the design index. Do not edit generated
sections by hand.

## Planned work

- Work only on a named plan or an explicitly identified off-plan task.
  Copy [plans/for-each-plan/](./plans/for-each-plan/plan.md) to start a plan.
  Record requirements in `spec.md` and cite their IDs in each step.
- Once the spec is approved, proceed through the steps. Diagnose and fix failed
  checks and dead ends within scope. Ask the user to decide when requirements
  conflict, scope must expand, or an action is outside the spec's authority.
- Acceptance checks in the spec are protected. Never weaken, skip or delete a
  check to make it pass. Escalate if a protected check cannot pass as written.
- Run plan work in Git worktrees. Concurrent steps must have no dependency
  between them and no overlap in `touches`. If in doubt, run them in sequence.
  After parallel steps merge, run the spec's combined validation.
- Mark a step done only when its evidence is recorded. Record unavailable verification.
  Store logs, locks and usage records outside the repository.
- Record whether a rule was retired, documentation was corrected, or a known
  violation was accepted. See the [spec template](./plans/for-each-plan/spec.md).

## Validation

Run the smallest check that proves the change. For changes to Markdown, plans,
memory or scripts, run `python3 scripts/check_context.py`.
