import type { APIRoute } from 'astro';

/** robots.txt; the sitemap line needs an absolute address, so it is written only when the origin is known. */
export const GET: APIRoute = ({ site }) => {
  const lines = ['User-agent: *', 'Allow: /', 'Disallow: /api/', 'Disallow: /data/'];
  if (process.env.SITE_URL && site) lines.push('', `Sitemap: ${site.origin}/sitemap-index.xml`);
  return new Response(`${lines.join('\n')}\n`, { headers: { 'content-type': 'text/plain; charset=utf-8' } });
};
