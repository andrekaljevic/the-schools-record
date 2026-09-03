/** Canonical paths for every route in the record. */

export const SCHOOL_SECTIONS = [
  ['exam-results', 'Examination results'],
  ['university-destinations', 'University outcomes'],
  ['oxbridge', 'Oxford and Cambridge'],
  ['us-universities', 'US and overseas universities'],
  ['school-entry', 'School entry'],
] as const;

export type SchoolSection = (typeof SCHOOL_SECTIONS)[number][0];

export const NAV = [
  ['Schools', '/schools/'],
  ['Compare', '/compare/'],
  ['Methodology', '/methodology/'],
  ['Evidence', '/evidence/'],
  ['Professional', '/professional/'],
] as const;

export const FOOTER_NAV = [
  ['About', '/about/'],
  ['Evidence centre', '/evidence/'],
  ['Oxford and Cambridge records', '/oxbridge/'],
  ['US university records', '/us-universities/'],
  ['Corrections', '/corrections/'],
  ['Privacy', '/privacy/'],
  ['Terms', '/terms/'],
  ['Changelog', '/changelog/'],
] as const;

/** Readable addresses for charted series; the metric id remains the state key everywhere else. */
export const seriesSlug = (metricId: string): string => (metricId === 'public-source-b6f5e1ed22afa0a6' ? 'oxbridge-destinations' : metricId.replace(/_/g, '-'));

export const schoolPath = (id: string, section?: SchoolSection): string =>
  section ? `/schools/${id}/${section}/` : `/schools/${id}/`;

/** `fig:winchester_gcse:3` → `/evidence/records/fig/winchester_gcse/3/` */
export const recordPath = (recordId: string): string => `/evidence/records/${recordId.split(':').join('/')}/`;

export const claimPath = (datasetId: string, period: string): string =>
  `/evidence/?dataset=${encodeURIComponent(datasetId)}&period=${encodeURIComponent(period)}`;

export const ledgerCsvPath = (datasetId: string): string => `/downloads/ledgers/${datasetId}.csv`;
export const compareCsvPath = (metricId: string): string => `/downloads/compare/${metricId}.csv`;

/**
 * Where a legacy Streamlit link (`/?p=/route&query`) now lives.  Used by the
 * inline redirect on the home and 404 pages and by the unit tests.
 */
export function legacyTarget(search: string): string | null {
  const params = new URLSearchParams(search);
  const route = params.get('p');
  if (!route || !route.startsWith('/')) return null;
  params.delete('p');
  let path = route.replace(/\/+$/, '');
  path = path === '' ? '/' : `${path}/`;
  if (path === '/evidence/' && params.get('record')) {
    const record = params.get('record') ?? '';
    params.delete('record');
    path = recordPath(record);
  }
  if (path === '/evidence/' && params.get('section') === 'sources') {
    params.delete('section');
    path = '/evidence/sources/';
  } else if (path === '/evidence/' && params.get('section') === 'method') {
    params.delete('section');
    path = '/evidence/method/';
  } else if (path === '/evidence/') {
    params.delete('section');
  }
  if (path === '/schools/' && params.get('series')) {
    const series = params.get('series') ?? '';
    params.delete('series');
    path = series === 'a_level_astar' ? '/schools/' : `/schools/series/${seriesSlug(series)}/`;
  }
  if (path === '/corrections/' && params.get('school')) {
    const school = params.get('school') ?? '';
    params.delete('school');
    path = `/corrections/schools/${school}/`;
  }
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}
