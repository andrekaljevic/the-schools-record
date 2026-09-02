/** Titles, descriptions and structured data for every route (port of tsr/meta.py). */
import { site } from './data';
import type { SchoolSummary } from './types';

export const SITE_NAME = 'The Schools Record';
export const DEFAULT_TITLE = `${SITE_NAME} | Independent school results, year by year`;
export const DEFAULT_DESCRIPTION =
  'A public, source-led record of examination results, university destinations and admissions evidence for seven leading UK independent schools, kept on their published definitions and never collapsed into a ranking.';

export interface PageMeta {
  title: string;
  description: string;
  /** Emit the schema.org Dataset description of the frozen record. */
  dataset?: boolean;
  /** Not indexed (utility pages, paginated listings beyond the first page). */
  noindex?: boolean;
}

export function titled(title: string): string {
  return `${title} | ${SITE_NAME}`;
}

export function datasetJsonLd(): Record<string, unknown> {
  const data = site();
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: 'The Schools Record · frozen public dataset',
    description: DEFAULT_DESCRIPTION,
    version: data.snapshot,
    temporalCoverage: `${data.spanFrom}/${data.spanTo}`,
    isAccessibleForFree: true,
    license:
      'Use figures only with the year, population, denominator, qualification, outcome type, evidence status and caveat displayed with them.',
    variableMeasured: [
      'Examination grade shares by qualification and scale',
      'University applications, offers and acceptances by entry cycle',
      'Leaver destinations by institution',
    ],
    size: `${data.counts.total} frozen records`,
    spatialCoverage: data.schools.map((school) => school.name),
  };
}

export function websiteJsonLd(origin: string): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE_NAME,
    url: `${origin}/`,
    description: DEFAULT_DESCRIPTION,
    publisher: { '@type': 'Organization', name: SITE_NAME, url: `${origin}/` },
  };
}

export function breadcrumbJsonLd(origin: string, crumbs: { label: string; href: string | null }[]): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [{ label: 'Home', href: '/' }, ...crumbs].map((crumb, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: crumb.label,
      ...(crumb.href ? { item: `${origin}${crumb.href}` } : {}),
    })),
  };
}

export function schoolMeta(school: SchoolSummary, section?: string): PageMeta {
  const sections: Record<string, [string, string]> = {
    'exam-results': ['Examination results', 'Published A-level, GCSE and IGCSE, IB and Cambridge Pre-U results, each on its published scale.'],
    'university-destinations': ['University outcomes', 'Applications, offers, acceptances and final destinations, kept apart.'],
    oxbridge: ['Oxford and Cambridge records', 'Apply-centre applications, offers and admissions by university and entry cycle.'],
    'us-universities': ['US and overseas university records', 'Named institutions, counts and outcome types by year.'],
    'school-entry': ['School entry', 'Published admissions process evidence and known gaps.'],
  };
  if (section && sections[section]) {
    const [label, description] = sections[section];
    return { title: titled(`${school.name} · ${label}`), description: `${school.name}: ${description}`, dataset: true };
  }
  return {
    title: titled(school.name),
    description: `${school.name} record, ${school.evidenceWindow}. ${school.oneLine}`.replace(/\s+/g, ' ').trim(),
    dataset: true,
  };
}
