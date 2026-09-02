import type { APIRoute, GetStaticPaths } from 'astro';
import { schools } from '../../../lib/data';

/** One CSV per ledger, exactly as the Python data layer serialises it. */
export const getStaticPaths = (() => {
  const seen = new Map<string, string>();
  for (const school of schools()) for (const ledger of [...school.exam, ...school.university]) seen.set(ledger.id, ledger.csv);
  return [...seen].map(([dataset, csv]) => ({ params: { dataset }, props: { csv } }));
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) =>
  new Response(String((props as { csv: string }).csv), { headers: { 'content-type': 'text/csv; charset=utf-8', 'content-disposition': 'attachment' } });
