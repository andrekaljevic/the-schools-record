import type { APIRoute } from 'astro';
import { searchIndex } from '../../lib/data';

/** The compact evidence index the search island fetches on demand. */
export const GET: APIRoute = () =>
  new Response(JSON.stringify(searchIndex()), { headers: { 'content-type': 'application/json; charset=utf-8' } });
