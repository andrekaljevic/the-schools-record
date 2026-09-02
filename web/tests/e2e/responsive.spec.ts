import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const VIEWPORTS = [[320, 568], [375, 812], [390, 844], [430, 932], [768, 1024], [1024, 768], [1280, 800], [1440, 900], [1920, 1080]] as const;
const ROUTES: Record<string, string> = {
  home: '/', schools: '/schools/', school: '/schools/westminster/', ledger: '/schools/winchester/exam-results/',
  compare: '/compare/?first=eton&second=westminster&metric=a_level_astar&from=2010&to=2019', evidence: '/evidence/',
  record: '/evidence/records/ox/oxford-apply-centre-2006-10092/', oxbridge: '/schools/eton/oxbridge/', corrections: '/corrections/',
  form: '/corrections/report/', dossier: '/sample-dossier/', 'not-found': '/404.html',
};
const OUT = process.env.SHOTS_DIR ?? 'test-results/viewports';
mkdirSync(OUT, { recursive: true });

for (const [width, height] of VIEWPORTS) {
  test(`no horizontal overflow and readable text at ${width}×${height}`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    for (const [name, route] of Object.entries(ROUTES)) {
      await page.goto(route);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, `${route} overflows by ${overflow}px at ${width}`).toBeLessThanOrEqual(1);
      const smallest = await page.evaluate(() => {
        let min = 99;
        for (const el of document.querySelectorAll('main p, main li, main td, main th, main a, main label')) {
          if (!(el instanceof HTMLElement) || el.offsetParent === null) continue;
          min = Math.min(min, parseFloat(getComputedStyle(el).fontSize));
        }
        return min;
      });
      expect(smallest, `${route} has text smaller than 11px at ${width}`).toBeGreaterThanOrEqual(11);
      await expect(page.locator('h1')).toBeVisible();
      if (process.env.SHOTS) await page.screenshot({ path: `${OUT}/${name}--${width}x${height}.png`, fullPage: width >= 1024 ? false : true });
    }
  });
}
