/** School index: live name filter and series navigation. Works without JavaScript (all rows shown). */
const form = document.querySelector<HTMLFormElement>('[data-island="school-index"]');
if (form) {
  const input = form.querySelector<HTMLInputElement>('input[type="search"]');
  const select = form.querySelector<HTMLSelectElement>('[data-series-select]');
  const rows = [...document.querySelectorAll<HTMLElement>('[data-index-list] .index-row')];
  const empty = document.querySelector<HTMLElement>('[data-empty]');
  const count = document.querySelector<HTMLElement>('[data-result-count]');
  const apply = (): void => {
    const needle = (input?.value ?? '').trim().toLowerCase();
    let shown = 0;
    for (const row of rows) {
      const hit = needle === '' || (row.dataset.name ?? '').includes(needle);
      row.hidden = !hit;
      if (hit) shown += 1;
    }
    if (empty) empty.hidden = shown > 0;
    if (count) count.textContent = `${shown} ${shown === 1 ? 'school' : 'schools'}`;
  };
  input?.addEventListener('input', apply);
  // The series select never navigates on its own (WCAG 3.2.2): the visitor confirms with the button.
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    apply();
    const option = select?.selectedOptions[0];
    const slug = option?.dataset.slug ?? select?.value ?? '';
    const current = form.dataset.current ?? '';
    if (select && select.value !== current) {
      const target = select.value === 'a_level_astar' ? '/schools/' : `/schools/series/${encodeURIComponent(slug)}/`;
      const query = input?.value.trim() ? `?q=${encodeURIComponent(input.value.trim())}` : '';
      window.location.assign(target + query);
    }
  });
  const initial = new URLSearchParams(window.location.search).get('q');
  if (initial && input) { input.value = initial; apply(); }
}

export {};
