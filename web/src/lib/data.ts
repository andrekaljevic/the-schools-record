/**
 * Build-time access to the public projection.
 *
 * The documents under src/generated/ are written by the Python data layer
 * (tools/build_public_projection.py) and are the only data this site reads.
 * They are loaded once per build and never mutated.
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import type {
  Compare,
  Corrections,
  Dossier,
  EvidenceRecord,
  IndexMetric,
  Manifest,
  Method,
  Oxbridge,
  School,
  SearchEntry,
  Site,
  SourceRegisterEntry,
  Us,
} from './types';

// Astro executes prerender chunks from dist/, so the projection is resolved from the
// project root (the working directory of `astro build`), not from this module's URL.
const GENERATED = `${resolve(process.env.TSR_PROJECTION_DIR ?? resolve(process.cwd(), 'src', 'generated'))}/`;
const cache = new Map<string, unknown>();

function load<T>(name: string): T {
  const hit = cache.get(name);
  if (hit !== undefined) return hit as T;
  const path = `${GENERATED}${name}.json`;
  if (!existsSync(path)) {
    throw new Error(
      `Projection document "${name}" is missing. Run \`npm run projection\` (python3 tools/build_public_projection.py) first.`,
    );
  }
  const parsed = JSON.parse(readFileSync(path, 'utf8')) as T;
  cache.set(name, parsed);
  return parsed;
}

export const site = (): Site => load<Site>('site');
export const manifest = (): Manifest => load<Manifest>('manifest');
export const indexPanels = (): Record<string, IndexMetric> => load('index-panels');
export const compare = (): Compare => load<Compare>('compare');
export const dossier = (): Dossier => load<Dossier>('dossier');
export const oxbridge = (): Oxbridge => load<Oxbridge>('oxbridge');
export const us = (): Us => load<Us>('us');
export const corrections = (): Corrections => load<Corrections>('corrections');
export const method = (): Method => load<Method>('method');
export const evidenceRecords = (): EvidenceRecord[] => load<EvidenceRecord[]>('evidence-records');
export const searchIndex = (): SearchEntry[] => load<SearchEntry[]>('evidence-search');
export const sourceRegister = (): SourceRegisterEntry[] => load<SourceRegisterEntry[]>('sources');
export const school = (id: string): School => load<School>(`schools/${id}`);
export const schools = (): School[] => site().schools.map((entry) => school(entry.id));

export function schoolSummary(id: string | null | undefined) {
  if (!id) return null;
  return site().schools.find((entry) => entry.id === id) ?? null;
}

let recordsById: Map<string, EvidenceRecord> | null = null;
export function evidenceRecord(id: string): EvidenceRecord | null {
  if (!recordsById) {
    recordsById = new Map(evidenceRecords().map((record) => [record.id, record]));
  }
  return recordsById.get(id) ?? null;
}

/** Records that carry one displayed ledger figure (dataset + period). */
export function recordsForClaim(datasetId: string, period: string): EvidenceRecord[] {
  return evidenceRecords().filter((record) => record.datasetId === datasetId && record.period === period);
}
