<script>
	// The accuracy view — the proof behind the Scorecard's numbers, one click deep.
	// Estimate vs truth, scored against quarantined ground truth. Method 0 sits beside
	// Method 1 in every figure; large error is displayed, not softened. Copy carries
	// the pre-registered claim language verbatim (docs/accuracy-spec.md §8).
	//
	// Imported at build time; written by src/incrementality/accuracy.py, which is the
	// one module that reads truth and publishes error metrics only — never truth.
	import accuracy from '$lib/data/accuracy.json';

	const { methods, stories } = accuracy;
	const m0 = methods.method0.headline;
	const m1 = methods.method1.headline;

	// toFixed(1) so trailing zeros show — JSON drops 22.0 to 22, and one decimal
	// everywhere is the rule on a measurement page (copy-audit).
	const pct = (x) => (x === null || x === undefined ? '—' : `${x.toFixed(1)}%`);
	const signed = (x) => (x === null || x === undefined ? '—' : `${x > 0 ? '+' : ''}${x.toFixed(1)}%`);
	const count = (n) => (n === null || n === undefined ? '—' : n.toLocaleString('en-US'));

	const STORY_LABELS = {
		pure_subsidy: 'Pure subsidy',
		hero_cannibal: 'Hero cannibal',
		pantry_trap: 'Pantry trap',
		clean_winner: 'Clean winner'
	};

	const REGIME_NAMES = {
		retailer: 'Retailer',
		promo_type: 'Promotion type',
		product_line: 'Product line',
		depth_band: 'Discount depth',
		duration_band: 'Duration',
		season: 'Season'
	};

	// Merge a shared regime feature's buckets across both methods, aligned by label.
	function sharedRegime(feature) {
		const b0 = Object.fromEntries(methods.method0.regimes[feature].map((b) => [b.label, b]));
		const b1 = Object.fromEntries(methods.method1.regimes[feature].map((b) => [b.label, b]));
		const labels = [...new Set([...Object.keys(b0), ...Object.keys(b1)])].sort();
		return labels.map((label) => ({ label, m0: b0[label], m1: b1[label] }));
	}
	const relaxRegime = methods.method1.regimes.match_relaxed_share ?? [];

	// Estimable = scored (measurable true lift) + below-floor (near-zero true lift).
	const estimable0 = m0.n_scored + m0.n_below_floor;
	const estimable1 = m1.n_scored + m1.n_below_floor;
	// Relaxation biases, read from the table so the prose can't drift from it.
	const relaxFully = relaxRegime.find((b) => b.label === 'fully relaxed');
	const relaxMixed = relaxRegime.find((b) => b.label === 'mixed');

	// --- Assortment (v0.7.0): launches and exits, scored against the data package's
	// pre-registered predictions (its SPEC §4.9.7; this repo's accuracy-spec §11).
	// Every figure and every hit/miss below is read from the artifact.
	const LIFE = 'launch (life weeks 1–13)';
	const LIFE_ORDER = ['continuing', LIFE, 'launch (after week 13)', 'exit fade (final 13 weeks)'];
	const SIB_ORDER = ['none', 'after same-line launch', 'after same-line exit', 'after both'];
	function orderedRegime(feature, order) {
		const b0 = Object.fromEntries(methods.method0.regimes[feature].map((b) => [b.label, b]));
		const b1 = Object.fromEntries(methods.method1.regimes[feature].map((b) => [b.label, b]));
		return order.filter((l) => b0[l] || b1[l]).map((label) => ({ label, m0: b0[label], m1: b1[label] }));
	}
	const lifeRows = orderedRegime('life_stage', LIFE_ORDER);
	const sibRows = orderedRegime('sibling_assortment', SIB_ORDER);

	const predictions = accuracy.predictions;
	const judged = predictions.flatMap((p) => [p.method0, p.method1]).filter((b) => b.outcome !== 'suppressed');
	const nHits = judged.filter((b) => b.outcome === 'hit').length;
	const OUTCOME = { hit: 'as predicted', miss: 'missed', suppressed: 'too few events' };

	const econ = (m) => Object.fromEntries(methods[m].life_stage_economics.map((b) => [b.label, b]));
	const econ0 = econ('method0');
	const econ1 = econ('method1');
	const lossRate = (b) => (b && b.n_estimable ? (100 * b.n_lost_money) / b.n_estimable : null);
	const econRows = LIFE_ORDER.filter((l) => econ0[l] || econ1[l]).map((label) => ({
		label,
		m0: econ0[label],
		m1: econ1[label]
	}));
	// Prediction 4, read per method: does the estimate keep launch promotions losing at
	// least as often as continuing ones, or does its launch-window error hide that?
	function keepsOrdering(e) {
		const launch = lossRate(e[LIFE]);
		const cont = lossRate(e.continuing);
		return launch !== null && cont !== null && launch >= cont;
	}
	const launchBias0 = lifeRows.find((r) => r.label === LIFE)?.m0?.median_signed_pct_error;
</script>

<svelte:head>
	<link rel="canonical" href="https://liftmath.lailarallc.com/accuracy" />
	<title>Lift Math — Accuracy</title>
	<meta
		name="description"
		content="How wrong the estimators actually are: error by regime against quarantined ground truth the estimation code provably never saw."
	/>
	<meta property="og:title" content="Lift Math — Accuracy" />
	<meta
		property="og:description"
		content="How wrong the estimators actually are — error by regime, scored against ground truth the estimation code provably never saw."
	/>
</svelte:head>

<div class="lailara-container accuracy">
	<p class="eyebrow">Accuracy · estimate vs truth</p>
	<a class="back" href="/">← Back to the Scorecard</a>

	<div class="ll-column">
		<h1 class="title">How wrong are these numbers?</h1>

		<p class="framing">
			Every incrementality tool asserts accuracy. This one measures it. The two baselines
			are scored against <strong>known ground truth</strong> — the error is shown, by
			regime, including where it is large. That is the whole claim, and it is a narrow one:
			<em>this is the error a standard method makes under a realistic, fully-known world.</em>
			It is not a prediction of the error on your data.
		</p>

		<p class="framing">
			The estimators are <strong>provably blind</strong> — enforced in code, not promised.
			An AST gate runs over every estimation file on every push; the generator's own
			coefficients are banned from the estimation path; and the git history shows both
			methods frozen and tagged <em>before</em> this page's code first read truth. The
			blindness claim is scoped exactly there — to the code — and nowhere wider.
		</p>
	</div>

	<!-- Headline: both methods side by side. Method 0 is never shown alone. -->
	<section class="headline">
		<h2 class="section-title">Median error, full population</h2>
		<div class="cards">
			<div class="method-card">
				<p class="method-name">Method 0 · pre-period</p>
				<p class="big">{pct(m0.median_abs_pct_error)}</p>
				<p class="big-note">median absolute error on incremental units</p>
				<p class="bias">Bias {signed(m0.median_signed_pct_error)} · {count(m0.n_scored)} events scored</p>
			</div>
			<div class="method-card">
				<p class="method-name">Method 1 · comparable-store</p>
				<p class="big">{pct(m1.median_abs_pct_error)}</p>
				<p class="big-note">median absolute error on incremental units</p>
				<p class="bias">Bias {signed(m1.median_signed_pct_error)} · {count(m1.n_scored)} events scored</p>
			</div>
		</div>
		<p class="excluded ll-measure">
			Scored covers the estimable events with a measurable true lift — {count(m0.n_scored)} of
			{count(estimable0)} for Method&nbsp;0, {count(m1.n_scored)} of {count(estimable1)} for Method&nbsp;1. The
			rest have true incremental below one unit — phantom and negligible-effect promotions,
			where a percentage of almost nothing is undefined — so they are set aside from the
			median, not hidden. The four seeded stories are included in these figures and also
			broken out below.
		</p>

		<p class="read ll-measure">
			Both methods over-credit promotions — the bias is positive for each. And the more
			defensible comparable-store method over-credits by more, not less. Two conclusions
			follow, both honest: the true promo book is worse than either method shows, and a
			better baseline is not automatically a better-calibrated one. A demonstration
			engineered to make the naive method lose would show neither.
		</p>
	</section>

	<!-- The four seeded stories, marked and separate — never folded into the headline. -->
	<section class="stories">
		<h2 class="section-title">The four seeded stories, scored separately</h2>
		<p class="section-sub ll-measure">
			These four events are planted outliers the tool is supposed to surface. They are
			reported here, apart from the headline median above — the honest denominator is the
			full population, not the outliers.
		</p>
		<div class="lailara-table-wrap">
			<table class="acc-table">
				<thead>
					<tr>
						<th scope="col">Story</th>
						<th class="col-num" scope="col">Method 0 error</th>
						<th class="col-num" scope="col">Method 1 error</th>
					</tr>
				</thead>
				<tbody>
					{#each stories as s (s.promo_id)}
						<tr>
							<td><span class="badge badge-story">{STORY_LABELS[s.story_tag]}</span> {s.promo_id}</td>
							<td class="col-num">{signed(s.method0.signed_pct_error)}</td>
							<td class="col-num">{signed(s.method1.signed_pct_error)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<!-- Error by regime — observed features only, ≥5 events per bucket. -->
	<section class="regimes">
		<h2 class="section-title">Error by regime</h2>
		<p class="section-sub ll-measure">
			Median absolute error, cut by observed features only — promotion type, depth,
			season and the like. No cut uses a truth-derived label, and every bucket holds at
			least five events, so no number reads back to an individual promotion.
		</p>

		{#each Object.entries(REGIME_NAMES) as [feature, name] (feature)}
			<div class="regime">
				<h3>{name}</h3>
				<div class="lailara-table-wrap">
					<table class="acc-table">
						<thead>
							<tr>
								<th scope="col">{name}</th>
								<th class="col-num" scope="col">Method 0</th>
								<th class="col-num" scope="col">Method 1</th>
							</tr>
						</thead>
						<tbody>
							{#each sharedRegime(feature) as row (row.label)}
								<tr>
									<td>{row.label}</td>
									<td class="col-num">{row.m0 ? pct(row.m0.median_abs_pct_error) : '—'}</td>
									<td class="col-num">{row.m1 ? pct(row.m1.median_abs_pct_error) : '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				{#if feature === 'promo_type'}
					<p class="regime-note">
						Coupon events have small true lifts, so percent error is measured against small
						denominators; the metric is stressed here, not just the method.
					</p>
				{/if}
			</div>
		{/each}

		{#if relaxRegime.length}
			<div class="regime">
				<h3>Match relaxation — Method 1 only</h3>
				<p class="section-sub ll-measure">
					Method 1 matches comparable stores by region, format class and volume; where the
						in-format pool is too thin it relaxes to region and volume alone. This cut asks
						whether the relaxation costs accuracy — and it does, on both axes: median error
						rises to {pct(relaxFully?.median_abs_pct_error)} for fully-relaxed matches against
						{pct(relaxMixed?.median_abs_pct_error)} for mixed, and the bias runs
						{signed(relaxFully?.median_signed_pct_error)} hot against
						{signed(relaxMixed?.median_signed_pct_error)}.
				</p>
				<div class="lailara-table-wrap">
					<table class="acc-table">
						<thead>
							<tr>
								<th scope="col">Match stratum</th>
								<th class="col-num" scope="col">Median error</th>
								<th class="col-num" scope="col">Bias</th>
								<th class="col-num" scope="col">Events</th>
							</tr>
						</thead>
						<tbody>
							{#each relaxRegime as b (b.label)}
								<tr>
									<td>{b.label}</td>
									<td class="col-num">{pct(b.median_abs_pct_error)}</td>
									<td class="col-num">{signed(b.median_signed_pct_error)}</td>
									<td class="col-num">{count(b.n_events)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	</section>

	<!-- Assortment epoch: launches and exits, against pre-registered predictions. -->
	<section class="assortment">
		<h2 class="section-title">Launches and exits — predicted before the data existed</h2>
		<p class="section-sub ll-measure">
			The portfolio now launches new items and retires old ones. A launch ramps up from
			nothing, an exit fades out, and either one shifts what its same-line siblings sell.
			Before generating that data, the data package wrote down where a standard baseline
			should go wrong around these moments. Each prediction is scored here against the
			frozen estimators: {nHits} of {judged.length} method-by-prediction checks went the
			predicted way. The misses are shown with the hits. Item life is read from scan
			presence alone — the first and last week an item sells.
		</p>
		<div class="lailara-table-wrap">
			<table class="acc-table">
				<thead>
					<tr>
						<th scope="col">Promotions</th>
						<th scope="col">Predicted bias</th>
						<th class="col-num" scope="col">Method 0</th>
						<th class="col-num" scope="col">Method 1</th>
					</tr>
				</thead>
				<tbody>
					{#each predictions as p (p.label)}
						<tr>
							<td>{p.label}</td>
							<td>{p.predicted_bias === 'high' ? 'over-credits' : 'under-credits'}</td>
							{#each [p.method0, p.method1] as b, i (i)}
								<td class="col-num">
									{#if b.outcome === 'suppressed'}
										{OUTCOME.suppressed}
									{:else}
										{signed(b.median_signed_pct_error)} · {OUTCOME[b.outcome]}
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="regime-note">
			Bias is the median signed error on the events in that group. Positive means the
			estimate credits the promotion with more lift than it had.
		</p>

		{#each [['Item life stage', lifeRows], ['Same-line launches and exits in the prior 13 weeks', sibRows]] as [name, rows] (name)}
			<div class="regime">
				<h3>{name}</h3>
				<div class="lailara-table-wrap">
					<table class="acc-table">
						<thead>
							<tr>
								<th scope="col">Group</th>
								<th class="col-num" scope="col">M0 error</th>
								<th class="col-num" scope="col">M0 bias</th>
								<th class="col-num" scope="col">M1 error</th>
								<th class="col-num" scope="col">M1 bias</th>
							</tr>
						</thead>
						<tbody>
							{#each rows as row (row.label)}
								<tr>
									<td>{row.label}</td>
									<td class="col-num">{row.m0 ? pct(row.m0.median_abs_pct_error) : '—'}</td>
									<td class="col-num">{row.m0 ? signed(row.m0.median_signed_pct_error) : '—'}</td>
									<td class="col-num">{row.m1 ? pct(row.m1.median_abs_pct_error) : '—'}</td>
									<td class="col-num">{row.m1 ? signed(row.m1.median_signed_pct_error) : '—'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/each}

		<div class="regime">
			<h3>Do launch promotions pay back? What each method concludes</h3>
			<p class="section-sub ll-measure">
				The data package measures true return on every promotion, on a ledger that does not
				depend on event order (each event's own lift minus the dip on its own item). Over each
				item's whole life, promotions on launched items lose money slightly more often than
				promotions on incumbent items: small, ramping bases carry fixed promotion costs. The
				figures below are a narrower slice and are estimates, not truth: promotions in a
				launched item's first 13 weeks against continuing items, counting only the events
				each method could estimate. Under Method 0, {lossRate(econ0[LIFE])?.toFixed(0)}% of estimable launch-window
				promotions lost money against {lossRate(econ0.continuing)?.toFixed(0)}% of continuing
				ones —
				{#if keepsOrdering(econ0)}
					the same ordering.
				{:else}
					the reverse ordering. Its launch-window bias of {signed(launchBias0)} is what hides it:
					a pre-period taken on the ramp understates the baseline.
				{/if}
				Under Method 1 the figures are {lossRate(econ1[LIFE])?.toFixed(0)}% and
				{lossRate(econ1.continuing)?.toFixed(0)}%{keepsOrdering(econ1)
					? ' — the ordering survives.'
					: ' — the ordering is lost here too.'}
				These are the methods’ own estimates, with their errors above.
			</p>
			<div class="lailara-table-wrap">
				<table class="acc-table">
					<thead>
						<tr>
							<th scope="col">Life stage</th>
							<th class="col-num" scope="col">M0 estimable</th>
							<th class="col-num" scope="col">M0 lost money</th>
							<th class="col-num" scope="col">M1 estimable</th>
							<th class="col-num" scope="col">M1 lost money</th>
						</tr>
					</thead>
					<tbody>
						{#each econRows as row (row.label)}
							<tr>
								<td>{row.label}</td>
								<td class="col-num">{count(row.m0.n_estimable)} of {count(row.m0.n_events)}</td>
								<td class="col-num">{lossRate(row.m0)?.toFixed(0) ?? '—'}%</td>
								<td class="col-num">{count(row.m1.n_estimable)} of {count(row.m1.n_events)}</td>
								<td class="col-num">{lossRate(row.m1)?.toFixed(0) ?? '—'}%</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</section>

	<p class="disclosure ll-measure">
		<strong>Synthetic data is the only honest testbed for this.</strong> It is at once the
		only world where truth is knowable and the only world that can be published: real
		client promotion data can never be shown, by any vendor, at any client count. Anyone
		claiming to demonstrate accuracy on real client data is either breaching
		confidentiality or making it up. The methodology and the deliverable are real; the
		data is synthetic, and that is the point.
	</p>
</div>

<style>
	.accuracy {
		font-family: var(--ll-sans);
		color: var(--ll-london-20);
	}
	.eyebrow {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--ll-red-42);
		margin: 0 0 var(--ll-space-sm);
	}
	.back {
		display: inline-block;
		font-size: 14px;
		color: var(--ll-london-20);
		text-decoration: underline;
		margin: 0 0 var(--ll-space-lg);
	}
	.back:hover {
		color: var(--ll-chicago-20);
	}
	.title {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2rem, 6vw, 3.5rem);
		line-height: 1.05;
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-lg);
	}
	.framing {
		font-size: 17px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0 0 var(--ll-space-base);
	}
	.section-title {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xs);
	}
	.section-sub {
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}
	section {
		margin-top: var(--ll-space-3xl);
		padding-top: var(--ll-space-2xl);
		border-top: 1px solid var(--ll-london-85);
	}
	.cards {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--ll-space-lg);
		margin: var(--ll-space-base) 0 var(--ll-space-lg);
	}
	.method-card {
		border: 1px solid var(--ll-london-85);
		border-radius: var(--ll-radius);
		padding: var(--ll-space-lg);
	}
	.method-name {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-sm);
	}
	.big {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2.25rem, 5vw, 3rem);
		letter-spacing: -0.02em;
		color: var(--ll-tokyo-40);
		margin: 0;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}
	.big-note {
		font-size: 13px;
		color: var(--ll-london-35);
		margin: var(--ll-space-xs) 0 var(--ll-space-sm);
	}
	.bias {
		font-size: 14px;
		font-weight: 600;
		color: var(--ll-london-20);
		margin: 0;
		font-variant-numeric: tabular-nums;
	}
	.read {
		font-size: 15px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0;
	}
	.excluded {
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}
	.regime-note {
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: var(--ll-space-sm) 0 0;
		max-width: var(--ll-body-max-width);
	}
	.acc-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 14px;
	}
	.acc-table thead th {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		text-align: left;
		padding: 0 var(--ll-space-base) var(--ll-space-sm);
		border-bottom: 2px solid var(--ll-london-5);
		white-space: nowrap;
	}
	.acc-table thead th.col-num {
		text-align: right;
	}
	.acc-table tbody td {
		padding: var(--ll-space-sm) var(--ll-space-base);
		border-bottom: 1px solid var(--ll-london-85);
		color: var(--ll-london-20);
	}
	.col-num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.regime {
		margin-top: var(--ll-space-lg);
	}
	.regime h3 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-sm);
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
	.disclosure {
		font-size: 14px;
		line-height: 1.6;
		color: var(--ll-london-35);
		margin: var(--ll-space-3xl) 0 0;
		padding-top: var(--ll-space-2xl);
		border-top: 1px solid var(--ll-london-85);
	}
	.lailara-table-wrap {
		overflow-x: auto;
		max-width: 100%;
		-webkit-overflow-scrolling: touch;
	}

	@media (max-width: 640px) {
		.cards {
			grid-template-columns: 1fr;
		}
	}
</style>
