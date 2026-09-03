/**
 * The research desk: search and filter every frozen record in the browser.
 * The compact index (/data/evidence-search.json) is fetched only when a search
 * or filter is used; until then the server-rendered first page stands, and the
 * static browse pages remain the no-JavaScript route through the record.
 */
import { esc } from '../lib/html';

interface Entry { id: string; c: string; sc: string | null; y: number | null; p: string; d: string; o: string; t: string; st: string; f: string; v: [string, string][]; q: string; ds: string | null }

const slugOf = (id: string) => id.split(':').map(encodeURIComponent).join('/');

const CORPUS: Record<string, string> = { figures: 'School results and destinations', granular: 'Subject and destination detail', oxbridge: 'Oxford and Cambridge admissions', us: 'US and overseas universities' };
const PAGE_SIZE = 25;

const form = document.querySelector<HTMLFormElement>('[data-island="evidence-search"]');
if (form) {
  const $ = <T extends HTMLElement>(selector: string) => document.querySelector<T>(selector) ?? missing(selector);
  const missing = (selector: string): never => { throw new Error(`evidence search: ${selector} is not on the page`); };
  const q = $<HTMLInputElement>('#ev-q');
  const corpus = $<HTMLSelectElement>('#ev-corpus');
  const school = $<HTMLSelectElement>('#ev-school');
  const domain = $<HTMLSelectElement>('#ev-domain');
  const status = $<HTMLSelectElement>('#ev-status');
  const from = $<HTMLInputElement>('#ev-from');
  const to = $<HTMLInputElement>('#ev-to');
  const results = $<HTMLElement>('[data-results]');
  const count = $<HTMLElement>('[data-result-count]');
  const pager = $<HTMLElement>('[data-pager]');
  const claim = $<HTMLElement>('[data-claim]');
  const schoolNames = new Map([...school.options].map((option) => [option.value, option.text]));
  const low = Number(form.dataset.low);
  const high = Number(form.dataset.high);

  let entries: Entry[] | null = null;
  let loading: Promise<Entry[]> | null = null;
  let page = 1;
  let claimState: { dataset: string; period: string } | null = null;

  function load(): Promise<Entry[]> {
    if (entries) return Promise.resolve(entries);
    if (!loading) {
      count.textContent = 'Loading the record index…';
      loading = fetch('/data/evidence-search.json').then((response) => {
        if (!response.ok) throw new Error(String(response.status));
        return response.json() as Promise<Entry[]>;
      }).then((data) => { entries = data; return data; }).catch((error: unknown) => {
        loading = null;
        count.textContent = 'The record index could not be loaded, so search is unavailable right now.';
        results.innerHTML = '<div class="empty-state"><h2>Search is unavailable</h2><p>Every record can still be read page by page: <a href="/evidence/browse/all/">browse all records</a>.</p></div>';
        throw error;
      });
    }
    return loading;
  }

  function readUrl(): boolean {
    const params = new URLSearchParams(window.location.search);
    q.value = params.get('q') ?? '';
    corpus.value = params.get('corpus') ?? '';
    school.value = params.get('school') ?? '';
    domain.value = params.get('domain') ?? '';
    status.value = params.get('status') ?? '';
    from.value = params.get('from') ?? '';
    to.value = params.get('to') ?? '';
    page = Math.max(1, Number.parseInt(params.get('page') ?? '1', 10) || 1);
    const dataset = params.get('dataset');
    const period = params.get('period');
    claimState = dataset && period ? { dataset, period } : null;
    if (claimState && !school.value && params.get('school')) school.value = params.get('school') ?? '';
    return Boolean(q.value || corpus.value || school.value || domain.value || status.value || from.value || to.value || claimState || page > 1);
  }

  const escapeAttr = esc;

  function writeUrl(): void {
    const params = new URLSearchParams();
    if (claimState) { params.set('dataset', claimState.dataset); params.set('period', claimState.period); }
    if (q.value.trim()) params.set('q', q.value.trim());
    if (corpus.value) params.set('corpus', corpus.value);
    if (school.value) params.set('school', school.value);
    if (domain.value) params.set('domain', domain.value);
    if (status.value) params.set('status', status.value);
    if (from.value) params.set('from', from.value);
    if (to.value) params.set('to', to.value);
    if (page > 1) params.set('page', String(page));
    const query = params.toString();
    window.history.replaceState(null, '', `/evidence/${query ? `?${query}` : ''}`);
  }

  function matches(entry: Entry, needle: string[]): boolean {
    if (claimState && (entry.ds !== claimState.dataset || entry.p !== claimState.period)) return false;
    if (corpus.value && entry.c !== corpus.value) return false;
    if (school.value && entry.sc !== school.value) return false;
    if (domain.value && entry.d !== domain.value) return false;
    if (status.value && entry.f !== status.value) return false;
    const yearFrom = from.value ? Number(from.value) : null;
    const yearTo = to.value ? Number(to.value) : null;
    if ((yearFrom !== null || yearTo !== null) && entry.y === null) return false;
    if (yearFrom !== null && entry.y !== null && entry.y < yearFrom) return false;
    if (yearTo !== null && entry.y !== null && entry.y > yearTo) return false;
    if (needle.length > 0) {
      const hay = `${entry.q} ${entry.t.toLowerCase()} ${entry.p.toLowerCase()}`;
      return needle.every((token) => hay.includes(token));
    }
    return true;
  }

  function card(entry: Entry): string {
    const schoolLink = entry.sc ? `<a href="/schools/${escapeAttr(entry.sc)}/">${esc(schoolNames.get(entry.sc) ?? entry.sc)}</a>` : '';
    const values = entry.v.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join('');
    const href = `/evidence/records/${slugOf(entry.id)}/`;
    return `<article class="evidence-record" id="${escapeAttr(entry.id)}">
      <header>
        <div class="record-kicker"><span class="status-pill status-pill-teal">${esc(CORPUS[entry.c] ?? entry.c)}</span><span>${esc(entry.o)}</span></div>
        <h2><a href="${escapeAttr(href)}">${esc(entry.t)}</a></h2>
        <p class="record-line">${schoolLink}${schoolLink ? ' · ' : ''}<span>${esc(entry.p)}</span> · <span class="record-status">Status: <a class="status-code" href="/evidence/method/#status-codes">${esc(entry.st)}</a></span></p>
      </header>
      <dl class="summary-list">${values}</dl>
      <p class="record-actions"><a class="text-link" href="${escapeAttr(href)}">Published fields, sources and where it is displayed</a></p>
    </article>`;
  }

  async function render(): Promise<void> {
    const data = await load();
    const needle = q.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const matched = data.filter((entry) => matches(entry, needle));
    const pages = Math.max(1, Math.ceil(matched.length / PAGE_SIZE));
    page = Math.min(page, pages);
    const start = (page - 1) * PAGE_SIZE;
    const shown = matched.slice(start, start + PAGE_SIZE);
    count.textContent = `${matched.length.toLocaleString('en-GB')} ${matched.length === 1 ? 'record' : 'records'}${matched.length > PAGE_SIZE ? ` · showing ${start + 1}–${start + shown.length}` : ''}`;
    results.innerHTML = shown.length > 0 ? shown.map(card).join('') : '<div class="empty-state"><h2>No matching records</h2><p>Try a school name, a different year or a broader search. A missing record is never manufactured.</p></div>';
    pager.hidden = pages <= 1;
    pager.innerHTML = `${page > 1 ? `<button type="button" class="text-link" data-page="${page - 1}">Previous</button>` : '<span></span>'}<span>Page ${page} of ${pages}</span>${page < pages ? `<button type="button" class="text-link" data-page="${page + 1}">Next</button>` : '<span></span>'}`;
    if (claimState) {
      claim.hidden = false;
      $<HTMLElement>('[data-claim-title]').textContent = `${claimState.dataset} · ${claimState.period}`;
      $<HTMLElement>('[data-claim-count]').textContent = `${matched.length} frozen ${matched.length === 1 ? 'record carries' : 'records carry'} this figure. Each is shown below with its published summary and a link to its public sources.`;
    } else {
      claim.hidden = true;
    }
    writeUrl();
  }

  let timer = 0;
  const run = (): void => { page = 1; void render().catch(() => undefined); };
  const schedule = (): void => { window.clearTimeout(timer); timer = window.setTimeout(run, 150); };
  q.addEventListener('input', schedule);
  for (const control of [corpus, school, domain, status, from, to]) control.addEventListener('change', run);
  form.addEventListener('submit', (event) => { event.preventDefault(); run(); });
  pager.addEventListener('click', (event) => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>('button[data-page]');
    if (!button) return;
    page = Number(button.dataset.page);
    void render().then(() => { count.setAttribute('tabindex', '-1'); count.focus(); count.scrollIntoView({ block: 'start' }); }).catch(() => undefined);
  });
  claim.querySelector('a')?.addEventListener('click', (event) => { event.preventDefault(); claimState = null; page = 1; void render().then(() => { count.setAttribute('tabindex', '-1'); count.focus(); }).catch(() => undefined); });
  from.min = String(low); to.max = String(high);
  if (readUrl()) void render().catch(() => undefined);
}

export {};
