/**
 * The comparison instrument.  State lives in the URL (?first&second&metric&from&to&view);
 * the chart is redrawn with the TypeScript port of the Python renderer, and the table,
 * legend, CSV link and notes follow.  Without JavaScript the page shows the default
 * comparison and the form submits as a plain GET.
 */
import { comparisonChart, type ChartMetric } from '../lib/chart';
import { formatPoint, clampInt } from '../lib/format';
import { esc } from '../lib/html';

interface Payload {
  yearMin: number;
  yearMax: number;
  schools: { id: string; name: string }[];
  metrics: { id: string; label: string; definition: string; note: string; unit: 'percent' | 'count'; points: { schoolId: string; year: number; value: number; status: string; datasetId: string; derived: boolean }[] }[];
}

const dataNode = document.getElementById('compare-data');
const form = document.querySelector<HTMLFormElement>('[data-island="compare"]');
if (dataNode && form) {
  const data = JSON.parse(dataNode.textContent ?? '{}') as Payload;
  const nameOf = (id: string) => data.schools.find((school) => school.id === id)?.name ?? id;
  const $ = <T extends Element>(selector: string) => document.querySelector<T>(selector);
  const first = $<HTMLSelectElement>('#compare-first')!;
  const second = $<HTMLSelectElement>('#compare-second')!;
  const metricSelect = $<HTMLSelectElement>('#compare-metric')!;
  const from = $<HTMLInputElement>('#compare-from')!;
  const to = $<HTMLInputElement>('#compare-to')!;
  const viewChart = $<HTMLInputElement>('#view-chart')!;
  const viewTable = $<HTMLInputElement>('#view-table')!;
  const chartNode = $<HTMLElement>('[data-chart]')!;
  const tableWrap = $<HTMLElement>('[data-table-wrap]')!;
  const tableBody = $<HTMLElement>('[data-table-body]')!;
  const tableCaption = $<HTMLElement>('[data-table-caption]')!;
  const legend = $<HTMLElement>('[data-legend]')!;
  const notComparable = $<HTMLElement>('[data-not-comparable]')!;
  const label = $<HTMLElement>('[data-metric-label]')!;
  const definition = $<HTMLElement>('[data-metric-definition]')!;
  const note = $<HTMLElement>('[data-metric-note]')!;
  const derivedNote = $<HTMLElement>('[data-derived-note]')!;
  const csv = $<HTMLAnchorElement>('[data-csv]')!;
  const share = $<HTMLElement>('[data-share-url]')!;
  const copy = $<HTMLButtonElement>('[data-copy-link]');

  const ids = data.schools.map((school) => school.id);
  const metricIds = data.metrics.map((metric) => metric.id);

  function readUrl(): void {
    const params = new URLSearchParams(window.location.search);
    const legacy = (params.get('schools') ?? '').split(',');
    const a = params.get('first') ?? legacy[0] ?? '';
    const b = params.get('second') ?? legacy[1] ?? '';
    if (ids.includes(a)) first.value = a;
    if (ids.includes(b)) second.value = b;
    const metric = params.get('metric') ?? '';
    if (metricIds.includes(metric)) metricSelect.value = metric;
    from.value = String(clampInt(params.get('from'), data.yearMin, data.yearMax, data.yearMin));
    to.value = String(clampInt(params.get('to'), data.yearMin, data.yearMax, data.yearMax));
    if (params.get('view') === 'table') viewTable.checked = true;
  }

  function state() {
    let a = first.value;
    let b = second.value;
    if (a === b) {
      b = ids.find((id) => id !== a) ?? b;
      second.value = b;
    }
    const yearFrom = clampInt(from.value, data.yearMin, data.yearMax, data.yearMin);
    const yearTo = Math.max(yearFrom, clampInt(to.value, data.yearMin, data.yearMax, data.yearMax));
    from.value = String(yearFrom);
    to.value = String(yearTo);
    const metric = data.metrics.find((item) => item.id === metricSelect.value) ?? data.metrics[0]!;
    return { a, b, yearFrom, yearTo, metric, view: viewTable.checked ? 'table' : 'chart' };
  }

  function render(pushState: boolean): void {
    const { a, b, yearFrom, yearTo, metric, view } = state();
    const points = metric.points.filter((point) => (point.schoolId === a || point.schoolId === b) && point.year >= yearFrom && point.year <= yearTo);
    const chartMetric: ChartMetric = {
      label: metric.label,
      unit: metric.unit,
      points: points.map((point) => ({ ...point, schoolName: nameOf(point.schoolId) })),
    };
    const years = new Map<number, Set<string>>();
    for (const point of points) years.set(point.year, (years.get(point.year) ?? new Set()).add(point.schoolId));
    const overlapping = [...years.values()].some((set) => set.size === 2);

    label.textContent = metric.label;
    definition.textContent = metric.definition;
    note.textContent = metric.note;
    derivedNote.hidden = !points.some((point) => point.derived);
    legend.innerHTML = `<span><i class="series-colour colour-1"></i>${esc(nameOf(a))}</span><span><i class="series-colour colour-2"></i>${esc(nameOf(b))}</span>`;
    notComparable.hidden = overlapping;
    chartNode.innerHTML = view === 'chart' && points.length > 0 ? comparisonChart(chartMetric, a, b, yearFrom, yearTo) : '';
    chartNode.hidden = view !== 'chart';
    tableWrap.className = view === 'table' ? 'comparison-table-visible' : 'comparison-table-accessible';
    tableCaption.textContent = `Exact values for ${metric.label}`;
    tableBody.innerHTML = points
      .map((point) => `<tr><th scope="row">${esc(nameOf(point.schoolId))}</th><td>${point.year}</td><td>${esc(formatPoint(point.value, metric.unit))}</td><td class="text">${esc(point.status)}</td></tr>`)
      .join('');
    csv.href = `/downloads/compare/${encodeURIComponent(metric.id)}.csv`;

    const params = new URLSearchParams({ first: a, second: b, metric: metric.id, from: String(yearFrom), to: String(yearTo) });
    if (view === 'table') params.set('view', 'table');
    const url = `/compare/?${params.toString()}`;
    share.textContent = url;
    if (pushState) window.history.replaceState(null, '', url);
  }

  readUrl();
  render(true);
  for (const control of [first, second, metricSelect, from, to, viewChart, viewTable]) {
    control.addEventListener('change', () => render(true));
  }
  form.addEventListener('submit', (event) => { event.preventDefault(); render(true); });
  window.addEventListener('popstate', () => { readUrl(); render(false); });
  if (copy && !navigator.clipboard) copy.remove();
  if (copy && navigator.clipboard) {
    copy.classList.remove('is-pending');
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(`${window.location.origin}${share.textContent ?? ''}`);
        copy.textContent = 'Link copied';
        window.setTimeout(() => { copy.textContent = 'Copy shareable link'; }, 2000);
      } catch { copy.textContent = 'Copy failed'; }
    });
  }
}

export {};
