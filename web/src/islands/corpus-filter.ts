/**
 * Client-side filtering of server-rendered corpus tables.  Rows carry data-*
 * attributes; a filter hides rows that do not match, empties whole family
 * blocks, and reflects the state in the URL.  Without JavaScript every row is
 * visible and the form submits as a plain GET the page ignores.
 */
const form = document.querySelector<HTMLFormElement>('[data-island="corpus-filter"]');
if (form) {
  const scope = document.querySelector<HTMLElement>('[data-filter-scope]')!;
  const shown = document.querySelector<HTMLElement>('[data-shown]');
  const empty = scope.querySelector<HTMLElement>('[data-empty]');
  const controls = [...form.querySelectorAll<HTMLInputElement | HTMLSelectElement>('[data-filter]')];
  const rows = [...scope.querySelectorAll<HTMLTableRowElement>('tbody tr')];

  function apply(): void {
    const state: Record<string, string> = {};
    for (const control of controls) state[control.dataset.filter ?? ''] = control.value.trim();
    const yearFrom = state['year-from'] ? Number(state['year-from']) : null;
    const yearTo = state['year-to'] ? Number(state['year-to']) : null;
    let visible = 0;
    for (const row of rows) {
      let hit = true;
      for (const [key, value] of Object.entries(state)) {
        if (!value || key.startsWith('year-')) continue;
        if ((row.dataset[key] ?? '') !== value) hit = false;
      }
      const year = row.dataset.year ? Number(row.dataset.year) : null;
      if (hit && (yearFrom !== null || yearTo !== null) && year !== null) {
        if (yearFrom !== null && year < yearFrom) hit = false;
        if (yearTo !== null && year > yearTo) hit = false;
      }
      row.hidden = !hit;
      if (hit) visible += 1;
    }
    for (const block of scope.querySelectorAll<HTMLElement>('[data-family]')) {
      if (!(block instanceof HTMLTableRowElement)) {
        const count = block.querySelectorAll('tbody tr:not([hidden])').length;
        block.hidden = count === 0;
        const label = block.querySelector<HTMLElement>('[data-family-count]');
        if (label) label.textContent = String(count);
      }
    }
    if (empty) empty.hidden = visible > 0;
    if (shown) shown.textContent = String(visible);
    const params = new URLSearchParams();
    for (const control of controls) if (control.value.trim()) params.set(control.name, control.value.trim());
    const query = params.toString();
    window.history.replaceState(null, '', `${window.location.pathname}${query ? `?${query}` : ''}`);
  }

  const params = new URLSearchParams(window.location.search);
  for (const control of controls) {
    const value = params.get(control.name);
    if (value !== null) control.value = value;
    control.addEventListener('change', apply);
    control.addEventListener('input', apply);
  }
  form.addEventListener('submit', (event) => { event.preventDefault(); apply(); });
  if ([...params.keys()].length > 0) apply();
}

export {};
