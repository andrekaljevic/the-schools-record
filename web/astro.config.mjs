// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// The origin is supplied by the deployment (SITE_URL). Without it the build
// carries no absolute address at all: no canonical, no Open Graph URL, no
// sitemap, so nothing can ever point at a placeholder or private host.
const site = process.env.SITE_URL || undefined;

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
  integrations: site ? [
    sitemap({
      // Listing pages beyond the first and the index series pages are noindex, so they stay out of the sitemap.
      filter: (page) => !page.includes('/404') && !page.includes('/downloads/') && !/\/evidence\/browse\/[^/]+\/\d+\/$/.test(page) && !page.includes('/schools/series/'),
      changefreq: 'monthly',
      priority: 0.6,
    }),
  ] : [],
  vite: {
    build: {
      sourcemap: false,
      assetsInlineLimit: 0,
    },
  },
});
