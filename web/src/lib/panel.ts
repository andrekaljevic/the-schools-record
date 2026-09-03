/**
 * Small-multiple panels, drawn exactly as tsr/chart.panel_svg draws them.
 *
 * The Python renderer is canonical; this port lets the comparison instrument
 * redraw in the browser on the same grammar as the index and school panels.
 * The parity test (tests/unit/chart-parity.test.ts) proves both renderers emit
 * identical SVG for every metric, school pair, window and layout in the record.
 */
import { esc } from './html';
import { toFixed } from './format';

export interface Layout {
  width: number;
  height: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
  font: number;
  ticks: number;
  grid: readonly number[];
  radius: number;
  stroke: number;
}

export interface PanelPoint {
  year: number;
  value: number;
  status: string;
}

export interface PanelSeries {
  label: string;
  points: readonly PanelPoint[];
  colour: string;
}

export interface Marker {
  kind: 'band' | 'rule';
  start: number;
  end: number;
  label: string;
  shortLabel: string;
}

export const COMPARISON_DESKTOP: Layout = { width: 860, height: 300, left: 56, right: 846, top: 24, bottom: 246, font: 12, ticks: 8, grid: [0, 0.25, 0.5, 0.75, 1], radius: 4, stroke: 2.5 };
export const COMPARISON_MOBILE: Layout = { width: 360, height: 236, left: 44, right: 350, top: 20, bottom: 190, font: 11, ticks: 4, grid: [0, 0.5, 1], radius: 3.2, stroke: 2 };
export const SERIES_COLOURS = ['#125c58', '#9a6d2e'] as const;
export const EXCEPTIONAL_YEARS: Marker = { kind: 'band', start: 2020, end: 2021, label: '2020–21 not drawn (CAG/TAG)', shortLabel: '2020–21' };

/** Python's round(): half to even. */
export function pyRound(value: number): number {
  const floor = Math.floor(value);
  const diff = value - floor;
  if (diff > 0.5) return floor + 1;
  if (diff < 0.5) return floor;
  return floor % 2 === 0 ? floor : floor + 1;
}

/**
 * Python's round(value, 2): the exact binary value correctly rounded to two
 * decimals, with exact ties going to the even hundredth.  A double is an exact
 * tie only when it is an odd multiple of 1/8 (the only three-decimal values
 * ending in 5 that binary can represent), and multiplying by 8 is exact, so
 * that test is safe; every other value is settled by toFixed, which rounds the
 * exact value.
 */
function pyRound2(value: number): number {
  const eighths = value * 8;
  if (Number.isInteger(eighths) && Math.abs(eighths % 2) === 1) {
    const lower = Math.floor(value * 100);
    const even = lower % 2 === 0 ? lower : lower + 1;
    return even / 100;
  }
  return Number(value.toFixed(2));
}

/** repr() of a float, or str() of an integral one. */
export function num(value: number): string {
  return String(value);
}

const coord = (value: number): string => num(pyRound2(value));

export function displayRange(yearFrom: number, yearTo: number): [number, number] {
  while (yearTo - yearFrom < 2) {
    yearFrom -= 1;
    yearTo += 1;
  }
  return [yearFrom, yearTo];
}

export function yearTicks(yearFrom: number, yearTo: number, target: number): number[] {
  const span = yearTo - yearFrom;
  const step = Math.max(1, Math.ceil(span / Math.max(1, target - 1)));
  const ticks: number[] = [];
  for (let year = yearFrom; year <= yearTo; year += step) ticks.push(year);
  const last = ticks[ticks.length - 1]!;
  if (last !== yearTo) {
    if ((yearTo - last) * 2 >= step) ticks.push(yearTo);
    else ticks[ticks.length - 1] = yearTo;
  }
  return ticks;
}

export function ceilingFor(values: readonly number[], unit: 'percent' | 'count'): number {
  if (unit === 'percent') return 100;
  const top = Math.max(1, ...values);
  const step = top <= 100 ? 10 : top <= 500 ? 50 : 100;
  return Math.max(step, Math.ceil(top / step) * step);
}

export function runs<T extends { year: number }>(points: readonly T[]): T[][] {
  const grouped: T[][] = [];
  for (const point of points) {
    const last = grouped[grouped.length - 1];
    if (last && point.year === last[last.length - 1]!.year + 1) last.push(point);
    else grouped.push([point]);
  }
  return grouped;
}

export function formatValue(value: number, unit: 'percent' | 'count'): string {
  return unit === 'percent' ? `${toFixed(value)}%` : value.toLocaleString('en-US');
}

function gridLabel(value: number, unit: 'percent' | 'count'): string {
  const rounded = pyRound(value);
  return unit === 'percent' ? `${rounded}%` : rounded.toLocaleString('en-US');
}

export function panelSvg(
  series: readonly PanelSeries[],
  yearFrom: number,
  yearTo: number,
  unit: 'percent' | 'count',
  layout: Layout,
  options: { uid: string; title: string; description: string; ceiling?: number; markers?: readonly Marker[]; cssClass?: string },
): string {
  [yearFrom, yearTo] = displayRange(yearFrom, yearTo);
  const values = series.flatMap((item) => item.points.map((point) => point.value));
  const top = options.ceiling ?? ceilingFor(values, unit);
  const x = (year: number): number => layout.left + ((year - yearFrom) / (yearTo - yearFrom)) * (layout.right - layout.left);
  const y = (value: number): number => layout.top + (1 - value / top) * (layout.bottom - layout.top);
  const parts: string[] = [];
  const short = layout.width < 500;

  for (const marker of options.markers ?? []) {
    if (marker.kind === 'band' && (marker.end < yearFrom || marker.start > yearTo)) continue;
    if (marker.kind === 'rule' && !(yearFrom < marker.start && marker.start <= yearTo)) continue;
    const label = esc(short ? marker.shortLabel : marker.label);
    if (marker.kind === 'band') {
      const x0 = x(Math.max(yearFrom, marker.start - 0.5));
      const x1 = x(Math.min(yearTo, marker.end + 0.5));
      parts.push(
        `<rect x="${coord(x0)}" y="${coord(layout.top)}" width="${coord(x1 - x0)}" height="${coord(layout.bottom - layout.top)}" class="panel-band"></rect>` +
          `<text x="${coord((x0 + x1) / 2)}" y="${coord(layout.top - 6)}" text-anchor="middle" class="panel-marker-label">${label}</text>`,
      );
    } else {
      const xr = x(marker.start - 0.5);
      parts.push(
        `<line x1="${coord(xr)}" x2="${coord(xr)}" y1="${coord(layout.top)}" y2="${coord(layout.bottom)}" class="panel-rule"></line>` +
          `<text x="${coord(xr + 5)}" y="${coord(layout.top - 6)}" text-anchor="start" class="panel-marker-label">${label}</text>`,
      );
    }
  }

  for (const fraction of layout.grid) {
    const value = top * fraction;
    const lineY = y(value);
    parts.push(
      `<g><line x1="${layout.left}" x2="${layout.right}" y1="${coord(lineY)}" y2="${coord(lineY)}" class="chart-gridline"></line>` +
        `<text x="${layout.left - 8}" y="${coord(lineY + layout.font * 0.35)}" text-anchor="end" class="panel-label">${esc(gridLabel(value, unit))}</text></g>`,
    );
  }

  const tickY = layout.height - 8;
  for (const year of yearTicks(yearFrom, yearTo, layout.ticks)) {
    parts.push(`<text x="${coord(x(year))}" y="${tickY}" text-anchor="middle" class="panel-label">${year}</text>`);
  }

  for (const item of series) {
    const points = [...item.points].sort((a, b) => a.year - b.year);
    for (const run of runs(points)) {
      if (run.length > 1) {
        const path = run.map((point) => `${coord(x(point.year))},${coord(y(point.value))}`).join(' L ');
        parts.push(`<path d="M ${path}" fill="none" stroke="${item.colour}" stroke-width="${num(layout.stroke)}" stroke-linejoin="round" stroke-linecap="round"></path>`);
      }
    }
    for (const point of points) {
      parts.push(
        `<circle cx="${coord(x(point.year))}" cy="${coord(y(point.value))}" r="${num(layout.radius)}" fill="${item.colour}">` +
          `<title>${esc(item.label)}, ${point.year}: ${esc(formatValue(point.value, unit))} · ${esc(point.status)}</title></circle>`,
      );
    }
  }

  const cssClass = options.cssClass ?? 'record-panel';
  return (
    `<svg class="${esc(cssClass)}" viewBox="0 0 ${layout.width} ${layout.height}" role="img" aria-labelledby="${esc(options.uid)}-title ${esc(options.uid)}-desc" style="font-size:${layout.font}px">` +
    `<title id="${esc(options.uid)}-title">${esc(options.title)}</title>` +
    `<desc id="${esc(options.uid)}-desc">${esc(options.description)}</desc>` +
    parts.join('') +
    '</svg>'
  );
}

export interface ComparisonMetric {
  id: string;
  label: string;
  unit: 'percent' | 'count';
  points: { schoolId: string; schoolName: string; year: number; value: number; status: string }[];
}

/** Two school series drawn on the panel grammar (tsr/chart.comparison_panel). */
export function comparisonPanel(
  metric: ComparisonMetric,
  first: string,
  second: string,
  yearFrom: number,
  yearTo: number,
  layout: Layout,
  options: { names?: Record<string, string>; markers?: readonly Marker[] } = {},
): string {
  const series: PanelSeries[] = [first, second].map((schoolId, index) => {
    const points = metric.points
      .filter((point) => point.schoolId === schoolId && point.year >= yearFrom && point.year <= yearTo)
      .sort((a, b) => a.year - b.year);
    const fallback = points[0]?.schoolName ?? schoolId;
    return { label: options.names?.[schoolId] ?? fallback, points, colour: SERIES_COLOURS[index] ?? SERIES_COLOURS[0] };
  });
  const mobile = layout.width < 500;
  return panelSvg(series, yearFrom, yearTo, metric.unit, layout, {
    uid: `comparison-${metric.id}-${mobile ? 'mobile' : 'desktop'}`,
    title: metric.label,
    description: `${series[0]!.label} and ${series[1]!.label}, ${yearFrom} to ${yearTo}. Lines join consecutive published years only. Exact values follow in the table.`,
    markers: options.markers ?? [],
    cssClass: `record-panel comparison-panel ${mobile ? 'panel-mobile' : 'panel-desktop'}`,
  });
}
