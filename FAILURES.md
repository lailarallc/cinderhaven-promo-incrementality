# cinderhaven-promo-incrementality — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

Worth carrying in from the data package build, because the pattern held four
times out of four: **every problem that looked like it needed a coefficient
tuned turned out to be a measurement or modelling error.** Nothing was ever
calibrated to hit a target. Expect the same here — an estimator whose error
looks wrong is more likely measuring the wrong thing than needing a knob.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search — e.g., "rendering, pandoc,
quarto" or "scope, scrollytelling, decoration"]

---

## Entries

### 2026-11-04 — Re-pin count pins were scattered across six test files

**Attempted:** Re-pin to v0.7.0 and update the contract counts in
`tests/test_data_contract.py` (events, rows, version), then run the suite.

**Why it didn't work:** The same counts (5,897 events, 1,340,462 rows, 5,735 / 5,122
estimable) were also hard-coded in test_anatomy, test_method0, test_method1,
test_scorecard and test_skeleton. Seven tests failed after the pipeline itself was green.

**What we did instead:** Grepped `tests/` for every old figure and updated all of them
(5,636 / 1,293,126 / 5,484 / 4,818). 94 green. On the next re-pin, grep `tests/` for the
old counts **before** running the suite, not after it fails.

**Status:** Resolved

**Tags:** re-pin, test-pins, counts, data-contract, pytest

### 2026-11-04 — Bash heredocs with Python `'''` strings failed to parse

**Attempted:** Patch files inline with `python - <<'EOF' ... EOF` where the Python used
`'''` triple-quoted replacement blocks.

**Why it didn't work:** The Bash tool's command parsing broke on the quote nesting
before Python ever ran.

**What we did instead:** Wrote each patch script to the session scratchpad and ran it
by path. Same pattern as the 2026-08-26 PowerShell entry: multi-line edits go through
a file, not a shell string.

**Status:** Resolved

**Tags:** bash, heredoc, quoting, tooling, editing

### 2026-09-01 — Cloudflare Pages `_redirects` SPA fallback shadowed the prerendered pages

**Attempted:** For Option B's partial prerender (~150 of 5,897 event pages), a
`web/static/_redirects` rule `/event/* /200.html 200` to serve the SPA shell for
non-prerendered events, with adapter-static `fallback: '200.html'`.

**Why it didn't work:** On Cloudflare Pages the catch-all `/event/*` rewrite fired
BEFORE the static-asset lookup, so it shadowed the prerendered files — a direct hit on a
PRERENDERED story page (`/event/PRE-0100`, whose `PRE-0100.html` existed with the correct
title/meta) 308-redirected to `/200` and served the generic shell. Humans got the client
render; crawlers and link previews got an empty shell — on exactly the deep-linked pages.
Static assets do NOT reliably win over a wildcard `_redirects` rewrite here.

**What we did instead:** Removed `_redirects` entirely and set adapter-static
`fallback: '404.html'`. Prerendered events then serve their own HTML (200); non-prerendered
events get the fallback shell, which Cloudflare serves with a 200 and the client router
renders from the event's fetched slice. Verified live: story page, a top-150 page, and a
non-prerendered page all correct.

**Status:** Resolved (Max's audit #2).

**Tags:** cloudflare-pages, adapter-static, prerender, spa-fallback, _redirects, seo,
option-b

---

### 2026-08-26 — PowerShell string-building mangled CRLF Svelte edits

**Attempted:** Insert multi-line markup/CSS into the CRLF `.svelte` files via
PowerShell — an array `-join "\`r\`n"` of `+`-concatenated elements, and
`.Replace(token, [char]0x2014)` to substitute glyphs (en/em dash, curly quote,
arrow).

**Why it didn't work:** The `-join` collapsed the bridge markup onto one line
(newlines lost), and `.Replace(string, char)` bound the `(char, char)` overload
— so the `~EN~`/`~EM~` glyph tokens were written literally. Root cause: these
files are CRLF with no `.gitattributes`, and the built-in Edit tool cannot match
them (it failed on every `.svelte` attempt), so all edits went through PowerShell
where the string/encoding quirks bit. Separately, `.` matches `\r` in .NET regex,
so `(?m)^(?=.)` re-indentation tabbed the "blank" lines (trailing-tab cleanup).

**What we did instead:** single-quoted here-string with `~T2~`/`~EM~` tokens,
normalize `\n`→`\r\n`, then token-substitute with explicit `([char]0x2014).ToString()`
glyphs; assert `loneLF=0` after every write. Lesson: check the file's EOL *first*
before editing these files.

**Status:** Resolved

**Tags:** powershell, crlf, svelte, string-encoding, editing, tooling

---

### 2026-08-22 — Reading `url.searchParams` in a component broke the prerender build

**Attempted:** Cross-view filters read from the URL via `$page.url.searchParams`
(Scorecard) and `$page.url.search` (event page), computed reactively so the list
filtered as the query changed.

**Why it didn't work:** `export const prerender = true` (required by
adapter-static) forbids reading the query string during SSR/prerender — the same
static file is served for every query, so the HTML cannot depend on it. The build
died: `Error: Cannot access url.searchParams on a page with prerendering enabled`,
`[500] GET /`.

**What we did instead:** read the URL **client-side only** — filters/method default
to empty/Method-0 in the prerendered HTML, and `onMount` reads
`new URLSearchParams(window.location.search)` after hydration; changes are written
back with `replaceState`. A brief unfiltered flash before hydration is acceptable on
an exploration surface.

**The lesson:** on a prerendered page, treat the query string as client-only state.
Anything that must render server-side belongs in the route params (path), not the
query — which is exactly why the per-event pages are `/event/[promo_id]` (path,
prerenderable via `entries()`) while filters are query (client-only).

**Status:** Resolved; both surfaces refactored to `onMount` reads.

**Tags:** sveltekit, prerender, adapter-static, url-searchparams, client-side,
cross-view-filters, near-miss

### 2026-08-19 — First method0 giveaway share divided retail dollars by manufacturer cost

**Attempted:** Implement §2.4 `subsidized_cost_share` literally as written —
`Σ(baseline_units × (regular − promoted)) / accrued_cost` — a per-row retail
giveaway summed and divided by the event's accrued trade cost.

**Why it didn't work:** mixed dimensions. The numerator is a **retail** discount
(shopper-side dollars); `accrued_cost` is the **manufacturer's** trade spend, only
0.55–0.69× the retail discount for scan_based and wildly variable (0.24–1.75×) for
billback/off_invoice. The ratio blew past 100% on 6 events, peaking at **936%** for
`clean_winner` — whose ~12%-of-volume coupon gives it the smallest subsidy base and
so the biggest blow-up. The display copy *"X% of trade dollars"* implies ≤100%, so
the number was not just ugly, it was incoherent.

**What we tried instead:** the volume ratio `Σ baseline_units / Σ observed_units`
over complied rows. Discount depth is constant within an event, so the discount
cancels and this is the dimensionally honest version of the same intent. For
scan-funded events it equals the dollar share identically (`accrued = rate ×
promoted units`); for fixed-funded events only the volume phrasing is honest.
Corrected in §2.4 and DECISIONS.md **before any scoring** — the pre-registration
ordering meant this was a pre-freeze correction, not a post-hoc re-run.

**The lesson, same as the upstream calibration bug (retail margin ≠ manufacturer
margin, ~2.8×):** retail prices decompose *cost*; they never share a denominator
with manufacturer trade dollars. A ratio whose most absurd value lands on the
smallest-base case is a dimension bug, not an outlier.

**Status:** Resolved before freeze; volume share written into §2.4 and method0.py.

**Tags:** modeling, giveaway-share, dimensions, retail-vs-manufacturer,
pre-registration, near-miss, method0

### 2026-08-18 — `pr.load()` raises on first call in any fresh install of v0.1.0

**Attempted:** Install `cinderhaven-promo-response` from the pinned git SHA
(`70021d4`, v0.1.0) into a clean venv and call `pr.load()` — the first line of
this project's consumer contract.

**Why it didn't work:** `generate.py:write_generation_block` unconditionally
reads `FIGURES.md` from the package root after writing the parquet artifacts.
`FIGURES.md` exists in the upstream **source repo** (4,605 bytes) but is **not
packaged into the wheel**, so in an installed package the path resolves to
`site-packages/FIGURES.md`, which does not exist:

    FileNotFoundError: [Errno 2] No such file or directory:
    '...\.venv\Lib\site-packages\FIGURES.md'

The failure is **deterministic on a cold cache and invisible afterwards.** The
crash happens *after* the artifacts are written, so the failed run leaves a
valid `.cache/` behind and the *second* call succeeds in ~0.9s. Verified by
moving `.cache/` aside and re-running: crash, then success. That is why it did
not surface as "the package is broken" — locally it looks like one bad run.

**Why it matters here, not just upstream:** every consumer that installs rather
than checks out hits this exactly once. **CI is a fresh container with a cold
cache every time**, so the data job fails on first `pr.load()` — permanently,
not flakily, since nothing persists the cache between runs. PLAN's instruction
to split the truth-gate job from the data job now has a second, concrete
reason: the gate is pure AST parsing and stays green regardless of this.

**What we tried instead:** Nothing yet — and deliberately not a local patch.
Editing the data package from this session is scope creep by CLAUDE.md; it is
released at v0.1.0 and lives in a separate repo. This is a finding logged here
and a release to plan there. Options for that release, not decided:
package `FIGURES.md` as package data, make `write_generation_block` a no-op
when the file is absent, or confine it to the source-checkout path.

**Workaround available if the CI task lands before that release:** call
`pr.load()` once and tolerate the first failure, or ship a warm cache. Both are
ugly; neither should be adopted without an entry in DECISIONS.md, because a
consumer that swallows an exception from its data package is exactly the kind
of silent-failure path this project's premise argues against.

**Defect class — this is the second instance, so it is a pattern, not an
incident.** *A file the package reads at runtime is not in the built artifact.*
Same class as the brand-fonts bug found in the 2026-07-28 portfolio audit:
`datascope` and `data-hygiene-auditor` shipped `brand_fonts/__init__.py` but
not the TTF/woff2 files, because `tool.setuptools.package-data` never declared
them. Font embedding worked from a source checkout and nowhere else.

The two failure *symptoms* are opposite, which is why the first one did not
teach the lesson: the fonts failed **silently** — `_font_face_css()` did
`if not path.exists(): continue`, so every pip-installed report fell back to
Georgia/Arial and the guarding test passed regardless. `FIGURES.md` fails
**loudly**, but only on a cold cache, and the crash leaves a working cache
behind that hides it on every subsequent call. Silent-and-always versus
loud-and-once. The shared cause is the same line of `pyproject.toml` in both
repos.

**The testable rule this yields, for the release checklist:** *every file the
package reads at runtime is present in the built artifact* — asserted against
the built wheel, not the source tree. Both bugs were invisible to a test run
from a checkout and both were caught, or would have been caught, by installing
the wheel into a clean environment and exercising the path that reads the file.
The 2026-07-28 audit verified this empirically against the built wheel; that is
the technique worth carrying forward.

**Status:** Open — upstream defect, unpatched. Local dev is unblocked (the
cache is warm). CI is blocked until the upstream release or a logged workaround.

**Tags:** upstream, cinderhaven-promo-response, packaging, FIGURES.md,
pr.load, cold-cache, ci, wheel, package-data

### 2026-08-19 — v0.2.0 economics() broke the consumer's --no-deps truth gate

**Attempted:** Ship `economics()` upstream (v0.2.0) with `import pandas` at the
top of `economics.py`, and `from .economics import economics` in the package
`__init__`.

**Why it didn't work:** That made `import cinderhaven_promo_response` require
pandas. The consumer's truth-gate CI job installs the package with `--no-deps`
(dependency-light, never flakes on wheel resolution) and imports it to run the
AST check — with no pandas present, the import raised and the gate job went red.
The consumer's own `Confirm the gate imported without its data layer` step
caught it on the re-pin push.

**What we tried instead:** v0.2.1 — import pandas lazily *inside* `economics()`,
restoring the package's import-without-pandas property. Added a regression test
that spawns a fresh interpreter, imports the package, and asserts pandas is
absent, so the property cannot regress silently. Consumer re-pinned v0.2.0 →
v0.2.1 (v0.2.0 was never green in CI, so it was superseded, not shipped).

**The pattern, now four-for-four:** the consumer gate caught the upstream defect,
the fix landed upstream with its own regression test, and nothing was papered
over downstream. Same shape as the FIGURES.md cold-cache catch and the
brand-fonts package-data catch — a downstream guard surfacing an upstream
packaging gap. See DECISIONS.md, "No downstream paper-over."

**Status:** Resolved (v0.2.1).

**Tags:** upstream, cinderhaven-promo-response, packaging, pandas, lazy-import,
--no-deps, truth-gate, regression, economics

### 2026-08-19 — First §2.4 draft mixed retail-price subsidy into a manufacturer-margin ROI

**Attempted:** Draft the Method 0 subsidy math as
`baseline_units × (regular_price − promoted_price)` netted against margin.

**Why it didn't work:** The ROI numerator is *manufacturer* margin
(wholesale − COGS), which never touches retail price; the shelf discount is the
retailer's move. Netting a retail-price giveaway against a manufacturer-margin
numerator double-counts (for scan_based the baseline subsidy is already inside
`accrued_cost`, the denominator). Caught during the #7 verification, before the
spec was frozen or tagged.

**What we tried instead:** Framing A — numerator is manufacturer margin on
incremental units; the giveaway is a *decomposition of accrued_cost* (the
denominator), displayed as a share of trade dollars, never netted. Same lesson
the upstream calibration bug taught (retail margin ≠ manufacturer margin, ~2.8x).

**Status:** Resolved before freeze; framing A written into docs/estimators.md §2.4.

**Tags:** modeling, roi, manufacturer-margin, subsidy, pre-registration, near-miss

### 2026-08-24 — Anatomy pre-rounded cross-view stats, so two pages showed different ROI for the same event

**Attempted:** `build_anatomy._float` rounded *every* float to one decimal — a
choice that is correct for the waterfall bar quantities (net is derived from the
rounded gross/baseline pair so the three bars reconcile on screen), but it was
also applied to `roi` and `subsidized_cost_share`.

**Why it didn't work:** the Scorecard carries those stats full-precision and the
shared view formatters round at display time (`roi.toFixed(2)`,
`Math.round(share*100)`). Pre-rounding in the artifact double-quantized them:
PRE-0002 M0 `roi` 0.5500704 → 0.6 rendered "0.60×" in Anatomy while the Scorecard
rendered "0.55×"; giveaway 0.6250662 → 0.6 (60%) vs 63%. `net_margin_cents` /
`accrued_cost_cents` stayed exact (`_int`), so the Anatomy page even contradicted
*itself* — $5,049/$9,180 = 0.55 printed above a 0.60 ROI. For a tool whose thesis
is "two numbers that should agree, don't," this is the one class of bug it cannot
ship.

**What we tried instead:** split the converter — `_units` keeps the 1-decimal
rounding for the bar quantities only; `_float` returns full precision, matching
`build_scorecard._float`, for the stats. Added `test_cross_view_consistency.py`:
every event × method × shared-stat, anatomy value ≡ scorecard emitted value,
exact — comparing the *emitted artifact values* (the only thing that catches
converter drift; both artifacts build from the same estimators, so comparing
estimator outputs would have missed it). Fix landed across commits `96a3a07`
(swept into a concurrent session's wrap, message silent on it) and is guarded
going forward by the new test.

**Lesson:** rounding is a *display* decision and belongs at the display layer, once.
An artifact consumed by shared formatters must carry full precision, or two
surfaces reading the same value render it differently. The measurement (the test
comparing emitted values) was again the right place to look — same instinct as the
upstream "suspect the measurement" rule.

**Status:** Resolved; guarded by test_cross_view_consistency.py (78 tests green).

**Tags:** rounding, cross-view-consistency, artifact-converter, anatomy, scorecard,
display-layer, determinism

[New entries get added here, most recent at the top]
