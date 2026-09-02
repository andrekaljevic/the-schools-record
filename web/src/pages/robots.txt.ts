import type { APIRoute } from 'astro';

/** robots.txt with an absolute sitemap address (the crawler specification requires one). */
export const GET: APIRoute = ({ site }) => {
  const origin = site ? site.origin : '';
  const body = ['User-agent: *', 'Allow: /', 'Disallow: /api/', 'Disallow: /data/', '', `Sitemap: ${origin}/sitemap-index.xml`, ''].join('\n');
  return new Response(body, { headers: { 'content-type': 'text/plain; charset=utf-8' } });
};
