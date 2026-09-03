// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// The production origin is supplied by the deployment (SITE_URL); the preview
// origin falls back to a placeholder so canonical URLs and the sitemap are
// always absolute and never point at a private host.
const site = process.env.SITE_URL || 'https://preview.the-schools-record.invalid';

export default defineConfig({
  site,
  output: 'static',
  trailingSlash: 'always',
  compressHTML: true,
  build: {
    format: 'directory',
    inlineStylesheets: 'never',
  },
  prefetch: false,
  integrations: [
    sitemap({
      // Listing pages beyond the first and the index series pages are noindex, so they stay out of the sitemap.
      filter: (page) => !page.includes('/404') && !page.includes('/downloads/') && !/\/evidence\/browse\/[^/]+\/\d+\/$/.test(page) && !page.includes('/schools/series/'),
      changefreq: 'monthly',
      priority: 0.6,
    }),
  ],
  vite: {
    build: {
      sourcemap: false,
      assetsInlineLimit: 0,
    },
  },
});
