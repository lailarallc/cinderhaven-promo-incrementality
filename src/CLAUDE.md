# Code conventions for this project's `src/`

This file applies when Claude is working in
`cinderhaven-promo-incrementality/src/`.

## The rule that outranks every other rule in this file

**Everything under `src/` is estimation code and is blind.** CI runs
`cinderhaven_promo_response.testing.assert_no_truth_access` over this
directory. One module — the accuracy view — is exempt by name, and it is the
only one that will ever be added to that exemption list.

Concretely, in this directory:

- No `from cinderhaven_promo_response import truth`, in any spelling.
- No string literal containing `truth-quarantine` or `promo_scan_truth`.
  The gate checks literals, not just imports, because
  `pd.read_parquet(".cache/truth-quarantine/...")` reaches truth without
  importing anything.
- No `import cinderhaven_promo_response.config` (nor `constants`, `baseline`,
  `assortment` — `tests/test_import_ban.py` enforces all four). **The gate will not catch
  this one.** That module holds the generator's own coefficients — lift
  centers, dip fractions, transfer coefficients — which is the answer key by
  another route. An estimator that reads it is not estimating.
- If an estimator needs a prior, derive it from observed data or cite an
  external source in a comment. Never from the generator.

If the gate blocks something you believe is legitimate, that is a decision to
log, not an exemption to add quietly.

## Style

- Match the existing code style. If there's a linter config, follow it strictly.
- New files mirror the structure of nearby existing files.
- No mixing of paradigms inside a module without a reason worth stating in DECISIONS.md.

## Naming

- Functions: verbs (`estimate_baseline`, `score_against_truth`)
- Variables: nouns (`event_roi`, `fitted_baseline`)
- Booleans: predicates (`is_complied`, `has_sufficient_pre_period`)
- Avoid abbreviations unless they're standard in this codebase.
- Use the data package's column names verbatim — `observed_units`,
  `week_ending`, `promo_id`. Renaming them in an intermediate frame is how a
  join silently produces the wrong shape.

## Imports

- Sort imports: external first, then internal absolute, then relative.
- No unused imports left in code.

## Comments

- Comment why, not what. The code already says what.
- Every modelling assumption gets a comment naming it as an assumption. An
  estimator is a pile of judgment calls; undocumented ones are indistinguishable
  from bugs.
- TODO comments include a date or issue reference.

## Determinism

- Same package version, same seed, same estimator → same numbers.
- No wall-clock, no unseeded randomness, no dict-ordering dependence in the
  estimation path. If a method needs randomness (bootstrap, cross-validation
  folds), seed it explicitly and record the seed alongside the result.

## Tests

- Each new non-trivial function gets at least one test in `tests/`.
- Test names describe behavior in plain English.
- Avoid testing implementation details — test inputs and outputs.
- An estimator's test asserts a *property* it should hold (monotonicity,
  units, sign, conservation), not a golden number copied from the last run.
  A golden number locks in whatever the code did, including bugs.

## Error handling

- Don't swallow errors. If you catch one, log or rethrow with context.
- No bare `except:` without a comment explaining why.
- Call `truth.assert_aligned_with_observed(delta)` before any accuracy number
  is computed. Observed rows from one generation scored against truth from
  another is the only completely silent failure in this pipeline — both files
  parse, both schemas validate, every number is wrong.

## Don't invent

- Before adding a new utility, check if a similar one already exists.
- Before adding a dependency, ask the user (and log to DECISIONS.md).
- Before refactoring an existing pattern, surface it as a question, not a fait accompli.

## When stuck

- Smallest reproducer.
- One change at a time.
- Run the test, read the actual output (not what you expected).
- If an estimator's error looks wrong, suspect the measurement before the
  model. In the upstream package that was the right call four times out of
  four — see FAILURES.md.
