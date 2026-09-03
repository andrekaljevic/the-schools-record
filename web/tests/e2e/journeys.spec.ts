import { test, expect } from '@playwright/test';

test('legacy Streamlit links redirect to canonical pages', async ({ page }) => {
  await page.goto('/?p=/schools/winchester/exam-results');
  await expect(page).toHaveURL(/\/schools\/winchester\/exam-results\/$/);
  await page.goto('/?p=/evidence&record=ox:oxford-apply-centre-2006-10092');
  await expect(page).toHaveURL(/\/evidence\/records\/ox\/oxford-apply-centre-2006-10092\/$/);
  await page.goto('/404.html?p=/compare&schools=eton,westminster&metric=a_level_astar&from=2010&to=2019');
  await expect(page).toHaveURL(/\/compare\/\?/);
  await expect(page.locator('#compare-first')).toHaveValue('eton');
  await expect(page.locator('#compare-second')).toHaveValue('westminster');
  await expect(page.locator('#compare-from')).toHaveValue('2010');
});

test('a parent follows a claim from a ledger row to its permanent record', async ({ page }) => {
  await page.goto('/schools/winchester/exam-results/#winchester_gcse-2016');
  const row = page.locator('#winchester_gcse-2016');
  await expect(row).toBeVisible();
  await expect(row.locator('th').first()).toHaveText('2016');
  await row.locator('summary').click();
  const permanent = row.locator('.evidence-actions a', { hasText: 'Permanent record' });
  await expect(permanent).toBeVisible();
  const href = await permanent.getAttribute('href');
  expect(href).toMatch(/^\/evidence\/records\/fig\/winchester_gcse\/\d+\/$/);
  await permanent.click();
  await expect(page.locator('h1')).toContainText('GCSE');
  await expect(page.locator('.record-line')).toContainText('2016');
  await expect(page.locator('.record-sources')).toBeVisible();
});

test('a ledger states its missing years and links a corrected row to its correction', async ({ page }) => {
  await page.goto('/schools/westminster/exam-results/');
  await expect(page.locator('.ledger-basis', { hasText: 'No row for' }).first()).toBeVisible();
  await page.goto('/schools/winchester/exam-results/#winchester_gcse-2016');
  await page.locator('#winchester_gcse-2016 summary').click();
  const correction = page.locator('#winchester_gcse-2016 .evidence-correction a').first();
  await expect(correction).toBeVisible();
  const id = await correction.textContent();
  await correction.click();
  await expect(page.locator(`#${id}`)).toBeVisible();
  await expect(page.locator(`#${id} .ledger-rows a`).first()).toBeVisible();
});

test('the ledger column toggle reveals every published column without JavaScript', async ({ page }) => {
  await page.goto('/schools/winchester/exam-results/');
  const ledger = page.locator('#winchester_pre_u_two_ruler_2011_2019');
  const hidden = ledger.locator('thead th.col-hidden');
  await expect(hidden.first()).toBeHidden();
  await ledger.locator('.ledger-toggle').check();
  await expect(hidden.first()).toBeVisible();
  const download = ledger.locator('a[download]');
  const response = await page.request.get((await download.getAttribute('href'))!);
  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toContain('text/csv');
  expect(await response.text()).toContain('2019');
});

test('the comparison instrument keeps state in the URL and redraws', async ({ page }) => {
  await page.goto('/compare/');
  await page.selectOption('#compare-metric', 'gcse_grade_9');
  await page.selectOption('#compare-first', 'westminster');
  await page.selectOption('#compare-second', 'kcs');
  await page.fill('#compare-from', '2018');
  await page.fill('#compare-to', '2019');
  await page.dispatchEvent('#compare-to', 'change');
  await expect(page).toHaveURL(/first=westminster&second=kcs&metric=gcse_grade_9&from=2018&to=2019/);
  await expect(page.locator('[data-metric-label]')).toContainText('grade 9');
  await expect(page.locator('[data-chart] svg.comparison-panel.panel-desktop')).toBeVisible();
  const circles = await page.locator('[data-chart] svg.panel-desktop circle').count();
  expect(circles).toBeGreaterThan(0);
  // A gap in publication is a gap in the line: no path joins non-consecutive years.
  await page.selectOption('#compare-metric', 'a_level_astar');
  await page.fill('#compare-from', '2015');
  await page.fill('#compare-to', '2024');
  await page.dispatchEvent('#compare-to', 'change');
  const joins = await page.locator('[data-chart] svg.panel-desktop path').evaluateAll((paths) => paths.map((path) => (path.getAttribute('d') ?? '').split(' L ').length));
  expect(Math.max(...joins)).toBeLessThanOrEqual(5);
  await expect(page.locator('[data-chart] svg.panel-desktop .panel-band')).toHaveCount(1);
  await page.click('label[for="view-table"]');
  await expect(page.locator('[data-table-wrap]')).toHaveClass(/comparison-table-visible/);
  await expect(page.locator('[data-table-body] tr').first()).toBeVisible();
  await expect(page).toHaveURL(/view=table/);
  // Choosing the same school twice is corrected, never rendered as a self-comparison.
  await page.selectOption('#compare-second', 'westminster');
  expect(await page.locator('#compare-second').inputValue()).not.toBe('westminster');
  const csv = await page.request.get('/downloads/compare/gcse_grade_9.csv');
  expect(csv.status()).toBe(200);
  expect(await csv.text()).toContain('Westminster School');
});

test('the evidence centre says so when its index cannot be loaded', async ({ page }) => {
  await page.route('**/data/evidence-search.json', (route) => route.fulfill({ status: 503, body: 'unavailable' }));
  await page.goto('/evidence/');
  await page.fill('#ev-q', 'eton');
  await expect(page.locator('[data-result-count]')).toContainText('could not be loaded');
  await expect(page.locator('[data-results] a[href="/evidence/browse/all/"]')).toBeVisible();
});

test('paging the evidence results keeps keyboard focus in the page', async ({ page }) => {
  await page.goto('/evidence/?corpus=oxbridge');
  await expect(page.locator('[data-result-count]')).toContainText('571');
  const next = page.locator('[data-pager] button', { hasText: 'Next' });
  await next.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-result-count]')).toContainText('26–50');
  await expect(page.locator('[data-result-count]')).toBeFocused();
});

test('the evidence centre searches, filters and traces a displayed figure', async ({ page }) => {
  await page.goto('/evidence/');
  await expect(page.locator('[data-results] .evidence-record')).toHaveCount(25);
  await page.fill('#ev-q', 'winchester pre-u 2015');
  await expect(page.locator('[data-result-count]')).not.toContainText('2,277', { timeout: 15_000 });
  const first = page.locator('[data-results] .evidence-record').first();
  await expect(first).toContainText('Winchester');
  await page.selectOption('#ev-corpus', 'oxbridge');
  await page.fill('#ev-q', '');
  await page.selectOption('#ev-school', 'eton');
  await expect(page).toHaveURL(/corpus=oxbridge/);
  await expect(page.locator('[data-result-count]')).toContainText('records');
  await page.goto('/evidence/?dataset=winchester_gcse&period=2016');
  await expect(page.locator('[data-claim]')).toBeVisible();
  await expect(page.locator('[data-claim-count]')).toContainText(/record/);
  await expect(page.locator('[data-results] .evidence-record').first()).toContainText('2016');
});

test('the school index filters by name and switches series', async ({ page }) => {
  await page.goto('/schools/');
  await page.fill('#school-search', 'winch');
  await expect(page.locator('[data-result-count]')).toHaveText('1 school');
  await expect(page.locator('.index-row:visible')).toHaveCount(1);
  await page.fill('#school-search', 'zzz');
  await expect(page.locator('[data-empty]')).toBeVisible();
  // Changing the series never navigates by itself; the visitor confirms with Apply.
  await page.selectOption('#index-series', 'gcse_grade_9');
  await expect(page).toHaveURL(/\/schools\/$/);
  await page.click('.index-controls button[type="submit"]');
  await expect(page).toHaveURL(/\/schools\/series\/gcse-grade-9\/\?q=zzz$/);
  await expect(page.locator('[data-empty]')).toBeVisible();
  await page.fill('#school-search', '');
  await expect(page.locator('.index-panel-empty').first()).toBeVisible();
});

test('the Oxbridge filters narrow the tables and empty families disappear', async ({ page }) => {
  await page.goto('/schools/eton/oxbridge/');
  const shown = page.locator('[data-shown]');
  const total = Number(await shown.textContent());
  await page.selectOption('#ox-family', 'apply_centre_outcomes');
  const after = Number(await shown.textContent());
  expect(after).toBeLessThan(total);
  await expect(page.locator('#oxbridge-school_published_oxbridge_offers')).toBeHidden();
  await page.fill('#ox-from', '2020');
  await page.dispatchEvent('#ox-from', 'input');
  const later = Number(await shown.textContent());
  expect(later).toBeLessThan(after);
  await expect(page).toHaveURL(/family=apply_centre_outcomes&from=2020/);
});

test('the correction form validates inline and never claims a submission was kept without a receiver', async ({ page }) => {
  await page.goto('/corrections/report/');
  await page.click('button[type="submit"]');
  await expect(page.locator('.field-error').first()).toBeVisible();
  await expect(page.locator('#cr-name')).toBeFocused();
  await page.fill('#cr-name', 'A Reader');
  await page.fill('#cr-email', 'reader@example.com');
  await page.fill('#cr-school', 'Winchester College');
  await page.fill('#cr-issue', 'The 2016 GCSE A* figure appears to be pre-remark.');
  await page.check('input[name="consent"]');
  await page.click('button[type="submit"]');
  const receipt = page.locator('[data-receipt]');
  await expect(receipt).toBeVisible();
  await expect(receipt).toContainText('Report not recorded');
  await expect(receipt).toContainText('could not be stored');
  await expect(receipt).toContainText('Winchester College');
  await expect(receipt).not.toContainText('received for review');
});

test('metadata, canonical links, structured data and sitemap are present', async ({ page, request }) => {
  await page.goto('/schools/eton/');
  await expect(page).toHaveTitle('Eton College | The Schools Record');
  // The build under test is made with SITE_URL set to the served origin; a placeholder host must never appear.
  const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
  expect(canonical).toBe('http://127.0.0.1:4321/schools/eton/');
  expect(await page.content()).not.toContain('.invalid');
  expect(await page.locator('meta[property="og:title"]').getAttribute('content')).toContain('Eton College');
  const ld = await page.locator('script[type="application/ld+json"]').allTextContents();
  expect(ld.some((text) => text.includes('"Dataset"'))).toBe(true);
  expect(ld.some((text) => text.includes('"BreadcrumbList"'))).toBe(true);
  const sitemap = await request.get('/sitemap-0.xml');
  expect(sitemap.status()).toBe(200);
  const xml = await sitemap.text();
  expect(xml).toContain('/schools/eton/');
  expect(xml).toContain('/evidence/records/ox/');
  expect(xml).not.toContain('/downloads/');
  expect(xml).not.toContain('/evidence/browse/all/2/');
  expect(xml).not.toContain('/schools/series/');
  const robots = await request.get('/robots.txt');
  expect(await robots.text()).toContain('Sitemap: http://127.0.0.1:4321/sitemap-index.xml');
  await page.goto('/404.html');
  await expect(page.locator('link[rel="canonical"]')).toHaveCount(0);
});

test('print styles hide navigation and expand the ledgers', async ({ page }) => {
  await page.emulateMedia({ media: 'print' });
  await page.goto('/sample-dossier/');
  await expect(page.locator('.site-header')).toBeHidden();
  await expect(page.locator('.dossier-actions')).toBeHidden();
  await expect(page.locator('.dossier-table')).toBeVisible();
  await page.goto('/schools/winchester/exam-results/');
  await expect(page.locator('#winchester_pre_u_two_ruler_2011_2019 thead th.col-hidden').first()).toBeVisible();
});

test('no page loads a third-party resource or sets a cookie', async ({ page, context }) => {
  const external: string[] = [];
  page.on('request', (request) => { const url = new URL(request.url()); if (url.host !== '127.0.0.1:4321') external.push(request.url()); });
  for (const route of ['/', '/compare/', '/evidence/', '/professional/']) await page.goto(route);
  expect(external).toEqual([]);
  expect(await context.cookies()).toEqual([]);
});
