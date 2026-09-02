import type { APIRoute, GetStaticPaths } from 'astro';
import { compare, site } from '../../../lib/data';

function csvCell(value: unknown): string {
  const text = String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** The full frozen series behind one comparison metric, every school and every year. */
export const getStaticPaths = (() => compare().metrics.map((metric) => ({ params: { metric: metric.id }, props: { metric } }))) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) => {
  const metric = (props as { metric: ReturnType<typeof compare>['metrics'][number] }).metric;
  const names = new Map(site().schools.map((school) => [school.id, school.name]));
  const lines = [['school', 'year', 'metric', 'value', 'unit', 'evidence_status', 'dataset', 'derived'].join(',')];
  for (const point of metric.points) {
    lines.push([names.get(point.schoolId) ?? point.schoolId, point.year, metric.label, point.value, metric.unit, point.status, point.datasetId, point.derived ? 'yes' : 'no'].map(csvCell).join(','));
  }
  return new Response(`${lines.join('\n')}\n`, { headers: { 'content-type': 'text/csv; charset=utf-8', 'content-disposition': 'attachment' } });
};
