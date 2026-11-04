<script>
	// The ROI Scorecard — the verdict, now over two baseline methods with a toggle.
	// First paint still reads in 30 seconds: verdict line, one chart, three numbers.
	// Method 0 (naive pre-period) is shown first — the anti-rigging exhibit — and the
	// toggle reveals Method 1 (comparable-store), with the delta between them visible.
	//
	// Imported at build time. The Python pipeline writes this file; a missing file
	// fails the build loudly rather than shipping stale numbers (build contract).
	import { onMount } from 'svelte';

	import { replaceState } from '$app/navigation';

	import scorecard from '$lib/data/scorecard.json';
	import { dollars, roiText, pct, count } from '$lib/format.js';
	import { FILTER_KEYS, parseFilters, matches, anyActive } from '$lib/filters.js';

	// Option B (DECISIONS 2026-08-27): the imported artifact carries the summary
	// (portfolios, precomputed chart tiers, filter options, cross-estimable counts) and
	// only the first page of the ranked list. The full ~5,900-event array is fetched
	// once, on the first filter touch or "show all", then cached for the session.
	const { portfolios, summary, first_page } = scorecard;
	// Scope-note ratios, computed by the pipeline from observed revenue (v0.7.0 re-run) —
	// they were hand-typed before and would have drifted with every re-pin.
	const spendCtx = summary.spend_context;

	let events = $state(first_page);
	let fullLoaded = $state(false);
	let loadingFull = $state(false);
	let loserMode = $state(false);

	async function ensureFullEvents() {
		if (fullLoaded || loadingFull) return;
		loadingFull = true;
		try {
			const res = await fetch('/scorecard-events.json');
			if (res.ok) {
				events = (await res.json()).events;
				fullLoaded = true;
			}
		} finally {
			loadingFull = false;
		}
	}
	function showAll() {
		ensureFullEvents();
		loserMode = false;
	}
	function showLosers() {
		ensureFullEvents();
		loserMode = true;
	}

	// Active baseline method — Method 0 leads (naive, shown first); the toggle switches
	// to Method 1 and everything follows. Declared early: the URL helpers below read it.
	let selected = $state('method0');

	// Cross-view filters, carried in the URL so they persist across the Scorecard and
	// the event pages. They narrow the ranked list only — the verdict header and the
	// distribution chart stay portfolio-wide (the 30-second read is the whole book).
	//
	// The URL is read CLIENT-SIDE only: a prerendered page cannot depend on the query
	// string (the same static file serves every query), so filters default to empty in
	// the prerendered HTML and are applied from the URL after hydration.
	let filters = $state({ retailer: '', line: '', type: '', status: '' });
	const filterOptions = summary.filter_options;
	const FILTER_LABELS = { retailer: 'Retailer', line: 'Product line', type: 'Promo type', status: 'Plan status' };
	const retailerLabel = (v) => v.replace('RET-', '');

	// The URL carries BOTH the filters and the active method, so a Scorecard row opens
	// its event page on the same method it was showing (a Method 0 row → a Method 0 page),
	// and returning restores the toggle. Read client-side only.
	function currentQuery() {
		const params = new URLSearchParams();
		for (const key of FILTER_KEYS) if (filters[key]) params.set(key, filters[key]);
		params.set('method', selected);
		return '?' + params.toString();
	}
	const stateQuery = $derived(currentQuery());

	onMount(() => {
		const sp = new URLSearchParams(window.location.search);
		filters = parseFilters(sp);
		const m = sp.get('method');
		if (m === 'method0' || m === 'method1') selected = m;
		// A deep-linked filter must narrow the full set, not just the first page.
		if (anyActive(filters)) ensureFullEvents();
	});

	function syncUrl() {
		replaceState(window.location.pathname + currentQuery(), {});
	}
	function setFilter(key, value) {
		ensureFullEvents();
		filters = { ...filters, [key]: value };
		syncUrl();
	}
	function clearFilters() {
		filters = { retailer: '', line: '', type: '', status: '' };
		syncUrl();
	}
	function selectMethod(key) {
		selected = key;
		syncUrl();
	}

	const METHOD_SHORT = { method0: 'Method 0', method1: 'Method 1' };
	const METHOD_TAG = {
		method0: 'Method 0 · pre-period',
		method1: 'Method 1 · comparable-store'
	};

	const otherKey = $derived(selected === 'method0' ? 'method1' : 'method0');
	// How many of THIS method's non-estimable events the other method can score.
	// Derived, never written down: the two methods exclude different events
	// (Method 1 gains one and loses another), so a hardcoded "some" or "one"
	// goes stale the moment either estimator's coverage shifts.
	const crossEstimable = $derived(summary.cross_estimable[selected]);
	const active = $derived(portfolios[selected]);
	const other = $derived(portfolios[otherKey]);

	const ledeText = $derived(
		selected === 'method0'
			? 'Method 0 is the most forgiving measure available — each promotion judged against the eight weeks before it. Even so, ' +
					count(active.n_lost_money) +
					' of ' +
					count(active.n_estimable) +
					' didn’t pay back. The portfolio clears ' +
					roiText(active.portfolio_roi) +
					' on the dollar, and the return is uneven — the top tenth of events produce ' + summary.net_margin_top_decile_share.method0 + '% of the net margin.'
			: 'Method 1 judges each promotion against comparable stores that didn’t run it — the stricter, concurrent test Method 0 is blind to. It clears ' +
					roiText(active.portfolio_roi) +
					' on the dollar. Toggle to Method 0 to see how much the naive pre-period read flatters the same promotions.'
	);

	// Chart tiers: counts precomputed in the artifact (Option B); labels + colors here.
	const TIER_META = [
		{ label: 'Lost money', color: 'var(--ll-tokyo-40)' },
		{ label: 'Returned 1–2×', color: 'var(--ll-hk-70)' },
		{ label: 'Returned 2–4×', color: 'var(--ll-hk-55)' },
		{ label: 'Returned 4×+', color: 'var(--ll-hk-20)' }
	];
	const tiers = $derived(summary.tiers[selected].map((n, i) => ({ ...TIER_META[i], n })));
	const maxTier = $derived(Math.max(...tiers.map((t) => t.n)));

	// Ranked event list, for the active method: estimable events by net margin; the
	// events this method cannot estimate are shown unranked below, never dropped
	// (spec 2.2, 3.5). Story labels mark the four seeded events; plan_status marks
	// phantom / unplanned. Marked, not claimed "found" — the Accuracy view's job.
	const STORY_LABELS = {
		pure_subsidy: 'Pure subsidy',
		hero_cannibal: 'Hero cannibal',
		pantry_trap: 'Pantry trap',
		clean_winner: 'Clean winner'
	};
	const rankedAll = $derived(
		events
			.filter((e) => e[selected].estimable && matches(e, filters) && (!loserMode || e[selected].lost_money))
			.slice()
			.sort((a, b) =>
				loserMode
					? a[selected].net_margin_cents - b[selected].net_margin_cents
					: b[selected].net_margin_cents - a[selected].net_margin_cents
			)
	);
	// Before the full fetch, cap the union first_page to the true top-N under the active
	// method; the loser view and any full view show everything fetched.
	const ranked = $derived(
		loserMode || fullLoaded ? rankedAll : rankedAll.slice(0, summary.first_page_size)
	);
	const unranked = $derived(events.filter((e) => !e[selected].estimable && matches(e, filters)));
	const totalEstimable = $derived(active.n_estimable);
	const filtersActive = $derived(anyActive(filters));

	// Table annotations, for the active method. Net-dip (spec 2.4): a giveaway share
	// > 1 means sales fell below the baseline during the promo — flagged, not a broken
	// percentage. Scan-funded phantoms accrue nothing, so their $0 spend and noisy
	// negative margin need a word (shared across methods).
	const isZeroPhantom = (e) => e.plan_status === 'phantom' && e.accrued_cost_cents === 0;
	const hasNetDip = $derived(ranked.some((e) => e[selected].baseline_exceeds_promoted));
	const hasZeroPhantom = $derived(ranked.some(isZeroPhantom));
</script>

<svelte:head>
	<link rel="canonical" href="https://liftmath.lailarallc.com/" />
	<title>Lift Math — ROI Scorecard</title>
	<meta property="og:title" content="Lift Math — ROI Scorecard" />
	<!-- The figure here is read from the artifact, not written down. A hardcoded
	     count is exactly what went stale in this page's own lede. -->
	<meta
		property="og:description"
		content="Trade-promotion incrementality, scored against known truth. {count(active.n_lost_money)} of {count(active.n_estimable)} promotions lost money under {METHOD_SHORT[selected]} — and the estimator's own error is on the page."
	/>
	<meta
		name="description"
		content="Portfolio trade spend, net incremental margin, and how many promotions did not pay back — under two baseline methods, both scored against known truth."
	/>
</svelte:head>

<div class="lailara-container">
	<section class="scorecard">
		<p class="eyebrow">ROI Scorecard</p>

		<div class="toggle" role="tablist" aria-label="Baseline method">
			{#each ['method0', 'method1'] as key (key)}
				<button
					role="tab"
					aria-selected={selected === key}
					class="toggle-btn"
					class:active={selected === key}
					onclick={() => selectMethod(key)}
				>
					{METHOD_TAG[key]}
				</button>
			{/each}
		</div>

		<div class="ll-column">
			<h1 class="verdict">{count(active.n_lost_money)} of {count(active.n_estimable)} promotions lost money.</h1>

			<p class="lede">{ledeText}</p>
		</div>

		<!-- Three numbers: the CFO header for the active method, each with the other
		     method's value beneath it so the delta is visible without toggling. -->
		<dl class="stats">
			<div class="stat">
				<dt>Trade spend</dt>
				<dd>{dollars(active.total_accrued_spend_cents)}</dd>
				<p class="stat-note">what these promotions actually cost, across the {count(active.n_estimable)} estimable events</p>
				<p class="stat-delta">{METHOD_SHORT[otherKey]}: {dollars(other.total_accrued_spend_cents)}</p>
			</div>
			<div class="stat">
				<dt>Net incremental margin</dt>
				<dd>{dollars(active.net_incremental_margin_cents)}</dd>
				<p class="stat-note">manufacturer margin on incremental units</p>
				<p class="stat-delta">{METHOD_SHORT[otherKey]}: {dollars(other.net_incremental_margin_cents)}</p>
			</div>
			<div class="stat stat--verdict">
				<dt>Portfolio ROI</dt>
				<dd>{roiText(active.portfolio_roi)}</dd>
				<p class="stat-note">margin returned per dollar of spend</p>
				<p class="stat-delta">{METHOD_SHORT[otherKey]}: {roiText(other.portfolio_roi)}</p>
			</div>
		</dl>

		<!-- "So what" bridge: why a checkable promo book matters, and the path to
		     the engagement. Static copy, frozen for audit. -->
		<section class="bridge">
			<p class="bridge-p ll-measure">Specialty food brands commit 15–20% of revenue to trade promotion, and the industry’s own benchmark says roughly seven in ten events don’t pay back. The reports brands receive almost never say so — because nobody can check them. This page is what checkable looks like: a full promo book, measured honestly, on a realistic $25M brand — with the measurement’s own error published one click away.</p>
			<p class="bridge-p ll-measure">The engagement version runs this same measurement on your promotion calendar and your POS data — and tells you which of your events would survive it.</p>
			<div class="bridge-cta">
				<a class="cta cta-primary" href="https://lailarallc.com/contact">Run this on your book →</a>
				<a class="cta cta-secondary" href="https://lailarallc.com/work/lift-math">Read the case study →</a>
			</div>
		</section>

		<p class="scope-note ll-measure">
			Trade spend here is the scan-promoted event slice of the trade book — accrued cost on promo
			events only. It excludes slotting, off-invoice allowances and deductions.
			Promotions carry {spendCtx.promoted_volume_pct.toFixed(1)}% of volume, so the portfolio
			totals hold up: trade spend is {spendCtx.spend_pct_of_total_revenue.toFixed(1)}% of total
			revenue and {spendCtx.spend_pct_of_promoted_revenue.toFixed(1)}% of promoted revenue — the
			event-level promotion allowance, not the all-in trade figure that folds in slotting and
			deductions this dataset does not carry.
		</p>

		<!-- One chart: where the estimable promotions landed under the active method. -->
		<figure class="chart">
			<figcaption>
				<h2>Where the {count(active.n_estimable)} estimable promotions landed</h2>
				<p class="chart-sub">Grouped by return on trade spend · {METHOD_TAG[selected]}</p>
			</figcaption>

			<div class="bars">
				{#each tiers as tier (tier.label)}
					<div class="bar-row">
						<span class="bar-label">{tier.label}</span>
						<div class="bar-track">
							<div class="bar-fill" style="width: {(tier.n / maxTier) * 100}%; background: {tier.color};"></div>
							<span class="bar-value">{tier.n}</span>
						</div>
					</div>
				{/each}
			</div>

			<p class="footnote">
				{count(active.n_events - active.n_estimable)} of {count(active.n_events)} events not estimable by
				{METHOD_SHORT[selected]}, shown unranked below and excluded from these totals. Method 0
				(naive pre-period) and Method 1 (comparable-store) are the two baselines on this site.
				Neither is the verdict — toggle to compare.
			</p>
		</figure>

		<!-- The proof behind the numbers, one click deep — not the front door. -->
		<a class="accuracy-link" href="/accuracy">
			<span class="accuracy-link-lead">How wrong are these numbers?</span>
			<span class="accuracy-link-sub"
				>See both methods scored against known truth — the error, by regime, including where
				it is large. →</span
			>
		</a>

		<!-- Ranked event list for the active method, with the other method's ROI per
		     row so the method delta is visible event by event. -->
		<section class="ranked">
			<h2 class="ranked-title">Every promotion, ranked by net margin</h2>
			<p class="ranked-sub">
				{count(active.n_estimable)} estimable events under {METHOD_SHORT[selected]}. Rows below
				break-even — margin under spend — are marked in the ROI column.
			</p>
						<p class="page-note">
				{#if loserMode}
					Showing the {count(active.n_lost_money)} promotions that lost money, worst first.
					<button class="show-all" onclick={showAll} disabled={loadingFull}>
						{loadingFull ? 'Loading…' : `Show all ${count(active.n_estimable)} estimable events`}
					</button>
				{:else if !fullLoaded}
					Showing the top {ranked.length} by net margin.
					<button class="show-all" onclick={showAll} disabled={loadingFull}>
						{loadingFull ? 'Loading…' : `Show all ${count(active.n_estimable)} estimable events`}
					</button>
					·
					<button class="show-all" onclick={showLosers} disabled={loadingFull}>Show the {count(active.n_lost_money)} that lost money</button>
				{:else}
					Showing all {count(active.n_estimable)} estimable events.
					<button class="show-all" onclick={showLosers} disabled={loadingFull}>Show the {count(active.n_lost_money)} that lost money</button>
				{/if}
			</p>

			<!-- Cross-view filters (URL state). Narrow the list; the verdict stays whole. -->
			<div class="filters" role="group" aria-label="Filter promotions">
				{#each FILTER_KEYS as key (key)}
					<label class="filter">
						<span class="filter-label">{FILTER_LABELS[key]}</span>
						<select value={filters[key]} onchange={(ev) => setFilter(key, ev.currentTarget.value)}>
							<option value="">All</option>
							{#each filterOptions[key] as opt (opt)}
								<option value={opt}>{key === 'retailer' ? retailerLabel(opt) : opt}</option>
							{/each}
						</select>
					</label>
				{/each}
				{#if filtersActive}
					<button class="clear" onclick={clearFilters}>Clear filters</button>
				{/if}
			</div>
			{#if filtersActive}
				<p class="filter-count">
					Showing {count(ranked.length)} of {count(totalEstimable)} estimable{unranked.length
						? ` · ${unranked.length} unranked`
						: ''}.
				</p>
			{/if}

			<div class="lailara-table-wrap">
				<table class="event-table">
					<thead>
						<tr>
							<th class="col-rank" scope="col">#</th>
							<th class="col-promo" scope="col">Promotion</th>
							<th class="col-num" scope="col">Net margin</th>
							<th class="col-num" scope="col">Trade spend</th>
							<th class="col-num" scope="col">ROI</th>
							<th class="col-num" scope="col">{METHOD_SHORT[otherKey]} ROI</th>
							<th class="col-num" scope="col">Giveaway</th>
						</tr>
					</thead>
					<tbody>
						{#each ranked as e, i (e.promo_id)}
							<tr class:lost={e[selected].lost_money}>
								<td class="col-rank">{i + 1}</td>
								<td class="col-promo">
									<span class="promo-head">
										<a class="promo-id" href="/event/{e.promo_id}{stateQuery}">{e.promo_id}</a>
										{#if STORY_LABELS[e.story_tag]}
											<span class="badge badge-story">{STORY_LABELS[e.story_tag]}</span>
										{/if}
										{#if e.plan_status !== 'executed'}
											<span class="badge badge-status">{e.plan_status}</span>
										{/if}
										{#if isZeroPhantom(e)}<sup class="mark">‡</sup>{/if}
									</span>
									<span class="promo-meta"
										>{e.retailer_id.replace('RET-', '')} · {e.sku} · {e.promo_type}</span
									>
								</td>
								<td class="col-num">{dollars(e[selected].net_margin_cents)}</td>
								<td class="col-num">{dollars(e.accrued_cost_cents)}</td>
								<td class="col-num roi" class:neg={e[selected].lost_money}
									>{roiText(e[selected].roi)}{#if e[selected].baseline_exceeds_promoted}<sup class="mark"
											>†</sup
										>{/if}</td
								>
								<td class="col-num other-roi">{roiText(e[otherKey].roi)}</td>
								<td class="col-num">{pct(e[selected].subsidized_cost_share)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			{#if hasNetDip || hasZeroPhantom}
				<ul class="table-notes ll-measure">
					{#if hasNetDip}
						<li>
							<span class="mark">†</span> Giveaway over 100%: sales during the promotion fell below
							the baseline — a dip — so the baseline volume outweighs what actually sold.
						</li>
					{/if}
					{#if hasZeroPhantom}
						<li>
							<span class="mark">‡</span> Scan-funded phantom — the promotion never ran, so nothing
							accrued; the margin shown is estimation noise around zero.
						</li>
					{/if}
				</ul>
			{/if}

			{#if unranked.length}
				<div class="unranked">
					<h3>Not estimable by {METHOD_SHORT[selected]}</h3>
					<p class="unranked-note ll-measure">
						{unranked.length}
						{unranked.length === 1 ? 'event' : 'events'}
						{selected === 'method0'
							? 'with too little pre-period history for a naive baseline'
							: 'with too few comparable control stores for a trustworthy median'}. Excluded from
						the totals above and shown here — the denominator is never hidden.
						{#if crossEstimable === 1}One of these is estimable under {METHOD_SHORT[otherKey]};
							toggle to see.{:else if crossEstimable}{crossEstimable} of these are estimable under
							{METHOD_SHORT[otherKey]}; toggle to see.{:else}None of these is estimable under
							{METHOD_SHORT[otherKey]} either.{/if}
						{METHOD_SHORT[otherKey]} excludes a different set, not a subset — the two methods
						fail on different events.
					</p>
					<ul>
						{#each unranked as e (e.promo_id)}
							<li>
								<a class="promo-id" href="/event/{e.promo_id}{stateQuery}">{e.promo_id}</a>
								<span class="promo-meta"
									>{e.retailer_id.replace('RET-', '')} · {e.sku} · {e.promo_type} ·
									{dollars(e.accrued_cost_cents)} spend</span
								>
							</li>
						{/each}
					</ul>
				</div>
			{/if}
		</section>
	</section>
</div>

<style>
	.scorecard {
		font-family: var(--ll-sans);
		color: var(--ll-london-20);
	}

	.eyebrow {
		font-family: var(--ll-sans);
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--ll-red-42);
		margin: 0 0 var(--ll-space-md);
	}

	/* Method toggle */
	.toggle {
		display: inline-flex;
		border: 1px solid var(--ll-london-85);
		border-radius: var(--ll-radius);
		overflow: hidden;
		margin: 0 0 var(--ll-space-lg);
	}
	.toggle-btn {
		font-family: var(--ll-sans);
		font-size: 13px;
		font-weight: 600;
		padding: 8px 16px;
		border: none;
		background: transparent;
		color: var(--ll-london-35);
		cursor: pointer;
	}
	.toggle-btn + .toggle-btn {
		border-left: 1px solid var(--ll-london-85);
	}
	.toggle-btn:hover {
		background: var(--ll-london-95);
	}
	.toggle-btn.active {
		background: var(--ll-chicago-20);
		color: #fff;
	}
	.toggle-btn:focus-visible {
		outline: 2px solid var(--ll-london-5);
		outline-offset: -2px;
	}

	.verdict {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2rem, 6vw, 3.5rem);
		line-height: 1.05;
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-base);
	}

	.lede {
		font-size: 17px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0 0 var(--ll-space-2xl);
	}

	/* Three numbers */
	.stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--ll-space-lg);
		margin: 0 0 var(--ll-space-base);
		padding: var(--ll-space-lg) 0;
		border-top: 1px solid var(--ll-london-85);
		border-bottom: 1px solid var(--ll-london-85);
	}
	.stat {
		margin: 0;
	}
	.stat dt {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-xs);
	}
	.stat dd {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.75rem, 4vw, 2.25rem);
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0;
		font-variant-numeric: tabular-nums;
		line-height: 1.1;
	}
	.stat--verdict dd {
		color: var(--ll-hk-25);
	}
	.stat-note {
		font-size: 13px;
		color: var(--ll-london-35);
		margin: var(--ll-space-xs) 0 0;
		line-height: 1.4;
	}
	.stat-delta {
		font-size: 13px;
		font-weight: 600;
		color: var(--ll-london-20);
		margin: var(--ll-space-xs) 0 0;
		font-variant-numeric: tabular-nums;
	}

	/* Scoping caveat under the three numbers — what "trade spend" does and doesn't cover. */
	.scope-note {
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-3xl);
	}

	/* "So what" bridge: the pitch under the numbers, before the chart. */
	.bridge {
		margin: var(--ll-space-lg) 0 var(--ll-space-3xl);
	}
	.bridge-p {
		font-size: 16px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0 0 var(--ll-space-base);
	}
	.bridge-cta {
		display: flex;
		flex-wrap: wrap;
		gap: var(--ll-space-md);
		margin-top: var(--ll-space-lg);
	}
	.cta {
		display: inline-block;
		font-family: var(--ll-sans);
		font-size: 15px;
		font-weight: 600;
		padding: 10px 18px;
		border-radius: var(--ll-radius);
		border: 1px solid var(--ll-chicago-20);
		text-decoration: none;
	}
	.cta-primary {
		background: var(--ll-chicago-20);
		color: #fff;
	}
	.cta-primary:hover {
		background: var(--ll-chicago-10);
	}
	.cta-secondary {
		background: transparent;
		color: var(--ll-chicago-20);
	}
	.cta-secondary:hover {
		background: var(--ll-chicago-95);
	}
	.cta:focus-visible {
		outline: 2px solid var(--ll-london-5);
		outline-offset: 2px;
	}

	/* One chart — DOM bars */
	.chart {
		margin: 0;
	}
	.chart figcaption h2 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xxs);
	}
	.chart-sub {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-lg);
	}
	.bars {
		display: flex;
		flex-direction: column;
		gap: var(--ll-space-md);
	}
	.bar-row {
		display: grid;
		grid-template-columns: 8.5rem 1fr;
		align-items: center;
		gap: var(--ll-space-base);
	}
	.bar-label {
		font-size: 14px;
		color: var(--ll-london-20);
		text-align: right;
	}
	.bar-track {
		display: flex;
		align-items: center;
		gap: var(--ll-space-sm);
	}
	.bar-fill {
		height: 1.5rem;
		border-radius: var(--ll-radius);
		min-width: 2px;
	}
	.bar-value {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-london-5);
		font-variant-numeric: tabular-nums;
	}
	.footnote {
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: var(--ll-space-lg) 0 0;
		max-width: var(--ll-body-max-width);
	}

	/* Link into the accuracy view — the proof behind the numbers */
	.accuracy-link {
		display: block;
		margin: var(--ll-space-2xl) 0 0;
		padding: var(--ll-space-lg);
		border: 1px solid var(--ll-chicago-20);
		border-radius: var(--ll-radius);
		text-decoration: none;
		background: var(--ll-chicago-95);
	}
	.accuracy-link:hover {
		background: var(--ll-chicago-85);
	}
	.accuracy-link-lead {
		display: block;
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.125rem, 2.5vw, 1.25rem);
		color: var(--ll-chicago-20);
		margin: 0 0 var(--ll-space-xxs);
	}
	.accuracy-link-sub {
		display: block;
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-20);
	}

	/* Ranked event list */
	.ranked {
		margin-top: var(--ll-space-3xl);
		padding-top: var(--ll-space-2xl);
		border-top: 1px solid var(--ll-london-85);
		font-family: var(--ll-sans);
	}
	.filters {
		display: flex;
		flex-wrap: wrap;
		gap: var(--ll-space-base);
		align-items: flex-end;
		margin: 0 0 var(--ll-space-base);
	}
	.filter {
		display: flex;
		flex-direction: column;
		gap: var(--ll-space-xxs);
	}
	.filter-label {
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
	}
	.filter select {
		font-family: var(--ll-sans);
		font-size: 14px;
		height: 36px;
		padding: 0 var(--ll-space-sm);
		border: 1px solid var(--ll-london-85);
		border-radius: var(--ll-radius);
		background: #fff;
		color: var(--ll-london-20);
	}
	.clear {
		font-family: var(--ll-sans);
		font-size: 14px;
		font-weight: 600;
		height: 36px;
		padding: 0 var(--ll-space-base);
		border: 1px solid var(--ll-chicago-20);
		border-radius: var(--ll-radius);
		background: transparent;
		color: var(--ll-chicago-20);
		cursor: pointer;
	}
	.clear:hover {
		background: var(--ll-chicago-95);
	}
	.filter-count {
		font-size: 13px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}

	.ranked-title {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xxs);
	}
	.ranked-sub {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-lg);
		max-width: var(--ll-body-max-width);
	}
	.lailara-table-wrap {
		overflow-x: auto;
		max-width: 100%;
		-webkit-overflow-scrolling: touch;
	}
	.event-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 14px;
	}
	.event-table thead th {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		padding: 0 var(--ll-space-base) var(--ll-space-sm);
		border-bottom: 2px solid var(--ll-london-5);
		white-space: nowrap;
	}
	.event-table tbody td {
		padding: var(--ll-space-md) var(--ll-space-base);
		border-bottom: 1px solid var(--ll-london-85);
		vertical-align: baseline;
		color: var(--ll-london-20);
	}
	.col-num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.col-rank {
		text-align: right;
		color: var(--ll-london-35);
		font-variant-numeric: tabular-nums;
		width: 2.5rem;
	}
	.col-promo {
		text-align: left;
	}
	.event-table tbody td:first-child {
		border-left: 3px solid transparent;
	}
	.event-table tbody tr.lost td:first-child {
		border-left-color: var(--ll-tokyo-40);
	}
	.roi.neg {
		color: var(--ll-tokyo-40);
		font-weight: 600;
	}
	.other-roi {
		color: var(--ll-london-35);
	}
	.mark {
		color: var(--ll-london-40);
		font-weight: 600;
	}
	sup.mark {
		font-size: 0.7em;
		padding-left: 1px;
	}
	.table-notes {
		list-style: none;
		padding: 0;
		margin: var(--ll-space-base) 0 0;
		display: grid;
		gap: var(--ll-space-xs);
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
	}
	.table-notes .mark {
		font-style: normal;
	}
	.promo-head {
		display: flex;
		align-items: center;
		gap: var(--ll-space-sm);
		flex-wrap: wrap;
	}
	.promo-id {
		font-weight: 600;
		color: var(--ll-london-5);
		text-decoration: none;
	}
	a.promo-id:hover {
		color: var(--ll-chicago-20);
		text-decoration: underline;
	}
	.promo-meta {
		display: block;
		font-size: 12px;
		color: var(--ll-london-35);
		margin-top: 2px;
	}
	.badge {
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.02em;
		padding: 1px 6px;
		border-radius: var(--ll-radius);
		white-space: nowrap;
	}
	.badge-story {
		background: var(--ll-chicago-95);
		color: var(--ll-chicago-20);
	}
	.badge-status {
		background: var(--ll-sg-95);
		color: var(--ll-sg-35);
		text-transform: capitalize;
	}
	.unranked {
		margin-top: var(--ll-space-2xl);
	}
	.unranked h3 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xs);
	}
	.unranked-note {
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}
	.unranked ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: var(--ll-space-sm);
	}
	.unranked li {
		padding-left: var(--ll-space-md);
		border-left: 3px solid var(--ll-london-70);
	}

	/* Phone-first: the header must fully work at 375px (DECISIONS.md). */
	@media (max-width: 640px) {
		.stats {
			grid-template-columns: 1fr;
			gap: var(--ll-space-base);
		}
		.bar-row {
			grid-template-columns: 1fr;
			gap: var(--ll-space-xxs);
		}
		.bar-label {
			text-align: left;
		}
		.toggle {
			display: flex;
			width: 100%;
		}
		.toggle-btn {
			flex: 1;
		}
	}
	.page-note {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}
	.show-all {
		font-family: var(--ll-sans);
		font-size: 14px;
		font-weight: 600;
		color: var(--ll-chicago-20);
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		text-decoration: underline;
	}
	.show-all:disabled {
		color: var(--ll-london-40);
		cursor: default;
	}
</style>
