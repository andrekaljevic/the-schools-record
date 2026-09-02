import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const ROUTES = [
  '/', '/schools/', '/schools/westminster/', '/schools/winchester/exam-results/', '/schools/st-pauls/university-destinations/',
  '/schools/eton/oxbridge/', '/schools/westminster/us-universities/', '/schools/kcs/school-entry/',
  '/compare/', '/evidence/', '/evidence/sources/', '/evidence/method/', '/evidence/records/ox/oxford-apply-centre-2006-10092/',
  '/oxbridge/', '/us-universities/', '/corrections/', '/corrections/report/', '/methodology/', '/professional/', '/sample-dossier/',
  '/about/', '/privacy/', '/terms/', '/changelog/', '/404.html',
];

for (const route of ROUTES) {
  test(`axe: ${route} has no WCAG 2.2 A/AA violations`, async ({ page }) => {
    await page.goto(route);
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']).analyze();
    const violations = results.violations.map((item) => `${item.id}: ${item.help} (${item.nodes.length} nodes; first: ${item.nodes[0]?.target.join(' ')})`);
    expect(violations, violations.join('\n')).toEqual([]);
  });
}

test('every page has one h1, a skip link that works and a main landmark', async ({ page }) => {
  for (const route of ['/', '/schools/eton/', '/compare/', '/evidence/']) {
    await page.goto(route);
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.locator('main#main-content')).toHaveCount(1);
    await page.keyboard.press('Tab');
    const skip = page.locator('.skip-link');
    await expect(skip).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/#main-content$/);
  }
});

test('the mobile menu opens with the keyboard and lists the primary routes', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/');
  const summary = page.locator('.mobile-menu summary');
  await expect(summary).toBeVisible();
  await summary.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.mobile-menu nav a')).toHaveCount(5);
  await expect(page.locator('.mobile-menu nav a').first()).toBeVisible();
});

test('reduced motion removes transitions', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const duration = await page.evaluate(() => getComputedStyle(document.querySelector('.button-primary')!).transitionDuration);
  expect(duration).toBe('0s');
});

test('200% zoom keeps the home page readable without horizontal scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/');
  await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
