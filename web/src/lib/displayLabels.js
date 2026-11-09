// Public display labels for trade partners (rule decided 2026-11-05, lailara-website
// DECISIONS): a Cinderhaven dollar figure never sits beside a real retailer name.
// The pipeline artifacts keep their platform IDs (RET-WALMART); only rendered text
// goes through here. The map is vendored from cinderhaven-data-platform
// (reference/retailer_display_labels.json); scripts/check_retailer_labels.py checks text.
import labels from '../../../reference/retailer_display_labels.json';

const LABELS = new Map(
	Object.entries({ ...labels.retailers, ...labels.distributors }).map(([id, p]) => [id, p.label])
);

/** Capitalized display label for a platform retailer ID (RET-WALMART). An ID not in
 *  the map loses its RET- prefix, as the views showed it before. */
export function retailerLabel(id) {
	const label = LABELS.get(id) ?? id.replace('RET-', '');
	return label.charAt(0).toUpperCase() + label.slice(1);
}

/** Sort comparator on the display label, so option order does not follow the names. */
export const byRetailerLabel = (a, b) => retailerLabel(a).localeCompare(retailerLabel(b));
