/**
 * The comparison chart, drawn exactly as tsr/chart.comparison_chart draws it.
 *
 * The Python renderer is canonical; this port exists so the comparison
 * instrument can redraw in the browser without a round trip.  The parity test
 * (tests/unit/chart-parity.test.ts) proves both renderers emit identical SVG
 * for every metric, school pair and year window in the frozen record.
 */
import { esc } from './html';
import { formatPoint } from './format';

export const SERIES_COLOURS = ['#125c58', '#9a6d2e'] as const;

export interface ChartPoint {
  schoolId: string;
  schoolName: string;
  year: number;
  value: number;
  status: string;
}

export interface ChartMetric {
  label: string;
  unit: 'percent' | 'count';
  points: ChartPoint[];
}

/** Render a coordinate the way Python's repr() renders the same float. */
export function num(value: number): string {
  if (Number.isInteger(value)) return String(value);
  // Python repr and JavaScript's shortest round-trip form agree for finite
  // doubles except for exponent notation, which these coordinates never reach.
  return String(value);
}

export function comparisonChart(
  metric: ChartMetric,
  first: string,
  second: string,
  yearFrom: number,
  yearTo: number,
): string {
  const points = metric.points.filter(
    (point) => (point.schoolId === first || point.schoolId === second) && point.year >= yearFrom && point.year <= yearTo,
  );
  const years = [...new Set(points.map((point) => point.year))].sort((a, b) => a - b);
  const ceiling = metric.unit === 'percent' ? 100 : Math.max(1, ...points.map((point) => point.value));

  const x = (year: number): number => 62 + ((year - yearFrom) / Math.max(1, yearTo - yearFrom)) * 810;
  const y = (value: number): number => 30 + (1 - value / Math.max(1, ceiling)) * 302;

  const grid: string[] = [];
  for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
    const value = ceiling * (1 - fraction);
    const lineY = 30 + fraction * 302;
    const label = metric.unit === 'percent' ? `${pyRound(value)}%` : String(pyRound(value));
    grid.push(
      `<g><line x1="62" x2="872" y1="${num(lineY)}" y2="${num(lineY)}" class="chart-gridline"></line>` +
        `<text x="50" y="${num(lineY + 4)}" text-anchor="end" class="chart-label">${esc(label)}</text></g>`,
    );
  }

  const step = Math.max(1, Math.ceil(years.length / 7));
  const ticks = years
    .map((year, index) =>
      index % step === 0 || years.length < 8
        ? `<text x="${num(x(year))}" y="368" text-anchor="middle" class="chart-label">${year}</text>`
        : '',
    )
    .join('');

  const series: string[] = [];
  [first, second].forEach((schoolId, index) => {
    const own = points.filter((point) => point.schoolId === schoolId).sort((a, b) => a.year - b.year);
    const colour = SERIES_COLOURS[index] ?? SERIES_COLOURS[0];
    let polyline = '';
    if (own.length > 1) {
      const path = own.map((point) => `${num(x(point.year))},${num(y(point.value))}`).join(' ');
      polyline = `<polyline points="${path}" fill="none" stroke="${colour}" stroke-width="3" stroke-linejoin="round"></polyline>`;
    }
    const circles = own
      .map(
        (point) =>
          `<circle cx="${num(x(point.year))}" cy="${num(y(point.value))}" r="5" fill="${colour}">` +
          `<title>${esc(point.schoolName)}, ${point.year}: ${esc(formatPoint(point.value, metric.unit))}</title></circle>`,
      )
      .join('');
    series.push(`<g>${polyline}${circles}</g>`);
  });

  return (
    `<div class="chart-wrap">\n  <svg class="comparison-chart" viewBox="0 0 900 390" role="img" aria-labelledby="chart-title chart-description">\n` +
    `    <title id="chart-title">${esc(metric.label)}</title>\n` +
    `    <desc id="chart-description">Two school series from ${yearFrom} to ${yearTo}. Exact values follow in the accessible table.</desc>\n` +
    `    ${grid.join('')}\n    ${ticks}\n    ${series.join('')}\n  </svg>\n</div>`
  );
}

/** Python's round(): banker's rounding to the nearest integer. */
function pyRound(value: number): number {
  const floor = Math.floor(value);
  const diff = value - floor;
  if (diff > 0.5) return floor + 1;
  if (diff < 0.5) return floor;
  return floor % 2 === 0 ? floor : floor + 1;
}
