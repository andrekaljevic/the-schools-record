/**
 * The comparison instrument.  State lives in the URL (?first&second&metric&from&to&view);
 * the panels are redrawn with the TypeScript port of the Python panel renderer, and the
 * pivoted table, legend, CSV link and notes follow.  Without JavaScript the page shows
 * the default comparison and its table.
 */
import { COMPARISON_DESKTOP, COMPARISON_MOBILE, comparisonPanel, formatValue, type Marker } from '../lib/panel';
import { clampInt } from '../lib/format';
import { esc } from '../lib/html';

interface Payload {
  yearMin: number;
  yearMax: number;
  schools: { id: string; name: string }[];
  metrics: { id: string; label: string; definition: string; note: string; unit: 'percent' | 'count'; markers: Marker[]; points: { schoolId: string; year: number; value: number; status: string; datasetId: string; derived: boolean }[] }[];
}

const dataNode = document.getElementById('compare-data');
const form = document.querySelector<HTMLFormElement>('[data-island="compare"]');

function hook<T extends Element>(selector: string): T | null {
  return document.querySelector<T>(selector);
}

if (dataNode && form) {
  const data = JSON.parse(dataNode.textContent ?? '{}') as Payload;
  const names = Object.fromEntries(data.schools.map((school) => [school.id, school.name]));
  const nameOf = (id: string) => names[id] ?? id;
  const first = hook<HTMLSelectElement>('#compare-first');
  const second = hook<HTMLSelectElement>('#compare-second');
  const metricSelect = hook<HTMLSelectElement>('#compare-metric');
  const from = hook<HTMLInputElement>('#compare-from');
  const to = hook<HTMLInputElement>('#compare-to');
  const viewChart = hook<HTMLInputElement>('#view-chart');
  const viewTable = hook<HTMLInputElement>('#view-table');
  const chartNode = hook<HTMLElement>('[data-chart]');
  const tableWrap = hook<HTMLElement>('[data-table-wrap]');
  const tableHead = hook<HTMLElement>('[data-table-head]');
  const tableBody = hook<HTMLElement>('[data-table-body]');
  const tableCaption = hook<HTMLElement>('[data-table-caption]');
  const legend = hook<HTMLElement>('[data-legend]');
  const notComparable = hook<HTMLElement>('[data-not-comparable]');
  const label = hook<HTMLElement>('[data-metric-label]');
  const definition = hook<HTMLElement>('[data-metric-definition]');
  const note = hook<HTMLElement>('[data-metric-note]');
  const derivedNote = hook<HTMLElement>('[data-derived-note]');
  const csv = hook<HTMLAnchorElement>('[data-csv]');
  const share = hook<HTMLElement>('[data-share-url]');
  const announce = hook<HTMLElement>('[data-announce]');
  const copy = hook<HTMLButtonElement>('[data-copy-link]');
  const ready = first && second && metricSelect && from && to && viewChart && viewTable && chartNode && tableWrap && tableHead && tableBody && tableCaption && legend && notComparable && label && definition && note && derivedNote && csv && share && announce;

  if (ready) {
    const ids = data.schools.map((school) => school.id);
    const metricIds = data.metrics.map((metric) => metric.id);

    const readUrl = (): void => {
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
    };

    const state = () => {
      const a = first.value;
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
    };

    const render = (): void => {
      const { a, b, yearFrom, yearTo, metric, view } = state();
      const points = metric.points.filter((point) => (point.schoolId === a || point.schoolId === b) && point.year >= yearFrom && point.year <= yearTo);
      const chartMetric = { id: metric.id, label: metric.label, unit: metric.unit, points: metric.points.map((point) => ({ ...point, schoolName: nameOf(point.schoolId) })) };
      const years = [...new Set(points.map((point) => point.year))].sort((x, y) => x - y);
      const overlapping = years.some((year) => points.filter((point) => point.year === year).length === 2);
      const at = (schoolId: string, year: number) => points.find((point) => point.schoolId === schoolId && point.year === year) ?? null;

      label.textContent = metric.label;
      definition.textContent = metric.definition;
      note.textContent = metric.note;
      derivedNote.hidden = !points.some((point) => point.derived);
      legend.innerHTML = `<span><i class="series-colour colour-1"></i>${esc(nameOf(a))}</span><span><i class="series-colour colour-2"></i>${esc(nameOf(b))}</span>`;
      notComparable.hidden = overlapping;
      chartNode.innerHTML = view === 'chart' && points.length > 0
        ? comparisonPanel(chartMetric, a, b, yearFrom, yearTo, COMPARISON_DESKTOP, { names, markers: metric.markers }) + comparisonPanel(chartMetric, a, b, yearFrom, yearTo, COMPARISON_MOBILE, { names, markers: metric.markers })
        : '';
      chartNode.hidden = view !== 'chart';
      tableWrap.className = view === 'table' ? 'comparison-table-visible' : 'comparison-table-accessible';
      tableCaption.textContent = `Exact values for ${metric.label}`;
      tableHead.innerHTML = `<tr><th scope="col">Year</th><th scope="col">${esc(nameOf(a))}</th><th scope="col">Status</th><th scope="col">${esc(nameOf(b))}</th><th scope="col">Status</th></tr>`;
      tableBody.innerHTML = years.map((year) => {
        const pa = at(a, year);
        const pb = at(b, year);
        const cell = (point: { value: number; status: string } | null) => point ? `<td>${esc(formatValue(point.value, metric.unit))}</td><td class="text">${esc(point.status)}</td>` : '<td class="blank-value">—</td><td class="text">—</td>';
        return `<tr><th scope="row">${year}</th>${cell(pa)}${cell(pb)}</tr>`;
      }).join('');
      csv.href = `/downloads/compare/${encodeURIComponent(metric.id)}.csv`;

      const params = new URLSearchParams({ first: a, second: b, metric: metric.id, from: String(yearFrom), to: String(yearTo) });
      if (view === 'table') params.set('view', 'table');
      const url = `/compare/?${params.toString()}`;
      share.innerHTML = esc(url).replace(/&amp;/g, '&amp;<wbr>');
      announce.textContent = `${metric.label}: ${nameOf(a)} and ${nameOf(b)}, ${yearFrom} to ${yearTo}, ${points.length} published ${points.length === 1 ? 'value' : 'values'}${overlapping ? '' : ', no overlapping years'}.`;
      window.history.replaceState(null, '', url);
    };

    readUrl();
    render();
    for (const control of [first, second, metricSelect, from, to, viewChart, viewTable]) control.addEventListener('change', render);
    form.addEventListener('submit', (event) => { event.preventDefault(); render(); });
    if (copy) {
      if (!navigator.clipboard) copy.remove();
      else {
        copy.classList.remove('is-pending');
        copy.addEventListener('click', async () => {
          try {
            await navigator.clipboard.writeText(`${window.location.origin}${window.location.pathname}${window.location.search}`);
            copy.textContent = 'Link copied';
            window.setTimeout(() => { copy.textContent = 'Copy shareable link'; }, 2000);
          } catch { copy.textContent = 'Copy failed'; }
        });
      }
    }
  }
}

export {};
