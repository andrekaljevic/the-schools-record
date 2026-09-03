/** Types of the public projection written by tools/build_public_projection.py. */

export interface SourceRef {
  ref: string;
  title: string;
  withheld: boolean;
  role: string | null;
  url: string | null;
}

export interface SchoolSummary {
  id: string;
  name: string;
  short: string;
  oneLine: string;
  evidenceWindow: string;
  latestVerifiedYear: number | null;
  datasetCount: number;
  counts: { figures: number; granular: number; oxbridge: number; us: number; total: number };
  artworkAlt: string;
  entryStatus: string | null;
  corrections: number;
  conflicts: number;
}

export interface Site {
  snapshot: string;
  baselineCommit: string;
  redactions: number;
  lastReviewed: string;
  lastReviewedShort: string;
  ledgersFrom: number;
  spanFrom: number;
  spanTo: number;
  counts: { figures: number; granular: number; oxbridge: number; us: number; total: number };
  corrections: number;
  conflicts: number;
  sourceReferences: number;
  schools: SchoolSummary[];
  sections: { key: string; label: string }[];
  corpusLabels: Record<string, string>;
  domainLabels: Record<string, string>;
}

export interface Manifest {
  datasetSha256: string;
  snapshot: string;
  baselineCommit: string;
  redactions: number;
  counts: Site['counts'];
  schools: number;
  documents: Record<string, string>;
}

export interface Field {
  key: string;
  label: string;
  kind: string;
}

export interface LedgerRow {
  index: number;
  anchor: string;
  period: string;
  year: number | null;
  status: string;
  note: string | null;
  cells: Record<string, string>;
  raw: Record<string, unknown>;
  blank: string[];
  sources: SourceRef[];
  datasetSourcesOmitted: number;
  corrections: string[];
  recordId: string;
}

export interface Ledger {
  id: string;
  label: string;
  family: string;
  domain: string;
  school: string;
  span: string;
  missingYears: number[];
  rowCount: number;
  basis: string | null;
  notes: string | string[] | null;
  fields: Field[];
  summaryFields: string[];
  hiddenFields: string[];
  rows: LedgerRow[];
  sources: SourceRef[];
  csv: string;
}

export interface GranularRow {
  index: number;
  total: boolean;
  cells: Record<string, string>;
  raw: Record<string, unknown>;
  blank: string[];
  recordId: string;
}

export interface GranularLedger {
  id: string;
  label: string;
  domain: string;
  period: string;
  rowCount: number;
  basis: string | null;
  fields: Field[];
  rows: GranularRow[];
  sourceTitle: string | null;
  asAt: string | null;
  sourceNote: string | null;
  sources: SourceRef[];
}

export interface LatestRecord {
  datasetId: string;
  label: string;
  family: string;
  year: number;
  period: string;
  anchor: string;
  values: { label: string; value: string }[];
  moreFields: number;
  status: string;
}

export interface TrajectoryPanel {
  key: string;
  qualification: string;
  label: string;
  denominator: string;
  first: number;
  last: number;
  series: { label: string; colour: string }[];
  note: string;
  svgDesktop: string;
  svgMobile: string;
  table: { year: number; values: (string | null)[]; status: string }[];
}

export interface Trajectory {
  panels: TrajectoryPanel[];
  notCharted: { label: string; span: string }[];
  yearFrom: number | null;
  yearTo: number | null;
  gapRule: string;
}

export interface InventoryRow {
  section: string;
  family: string;
  label: string;
  href: string;
  span: string;
  scales: string;
  rows: number;
}

export interface EntryProcess {
  status: string;
  freshness: string;
  entryPoints?: string[];
  steps?: { label: string; detail: string }[];
  limit?: string;
  sourceTitle?: string | null;
}

export interface School extends SchoolSummary {
  caution: string;
  spanFrom: number;
  spanTo: number;
  examLedgers: number;
  examRows: number;
  examFamilies: string[];
  universityLedgers: number;
  universityRows: number;
  universityFamilies: string[];
  oxbridgeSpan: string | null;
  usSpan: string | null;
  entryFreshness: string | null;
  latestExam: LatestRecord | null;
  latestUniversity: LatestRecord | null;
  trajectory: Trajectory;
  inventory: InventoryRow[];
  exam: Ledger[];
  university: Ledger[];
  granularExam: GranularLedger[];
  granularUniversity: GranularLedger[];
  entry: EntryProcess | null;
}

export interface IndexPanel {
  svg: string;
  latest: { value: string; year: number; status: string };
  count: number;
  table: { year: number; value: string; status: string }[];
}

export interface IndexMetric {
  id: string;
  slug: string;
  label: string;
  shortLabel: string;
  definition: string;
  note: string;
  unit: 'percent' | 'count';
  domain: string;
  derived: boolean;
  frame: { year_from: number; year_to: number; ceiling: number };
  panels: Record<string, IndexPanel | null>;
}

export interface MetricPoint {
  schoolId: string;
  year: number;
  value: number;
  status: string;
  datasetId: string;
  derived: boolean;
}

export interface ChartMarker {
  kind: 'band' | 'rule';
  start: number;
  end: number;
  label: string;
  shortLabel: string;
}

export interface Metric {
  id: string;
  label: string;
  shortLabel: string;
  definition: string;
  note: string;
  domain: string;
  unit: 'percent' | 'count';
  markers: ChartMarker[];
  points: MetricPoint[];
}

export interface Compare {
  yearMin: number;
  yearMax: number;
  defaultMetric: string;
  defaultSchools: string[];
  metrics: Metric[];
  gapRule: string;
  defaultSvgDesktop: string;
  defaultSvgMobile: string;
}

export interface Dossier {
  metric: { id: string; label: string; definition: string; note: string };
  rows: { year: number; eton: { value: string; status: string } | null; westminster: { value: string; status: string } | null }[];
  svgDesktop: string;
  svgMobile: string;
  prepared: string;
}

export interface OxbridgeRow {
  recordId: string;
  slug: string;
  family: string;
  familyLabel: string;
  scope: string;
  schoolId: string | null;
  year: number | null;
  cycle: number | null;
  institution: string | null;
  applyCentre: string | null;
  schoolName: string | null;
  subject: string | null;
  dimension: string | null;
  dimensionValue: string | null;
  periodStart: string | number | null;
  periodEnd: string | number | null;
  periodBasis: string | null;
  applications: string;
  offers: string;
  accepted: string;
  shortlisted: string;
  offerHolders: string;
  interviewed: string;
  offerRate: string;
  acceptedRate: string;
  applicantsPerPlace: string | number | null;
  oxfordOffers: string;
  cambridgeOffers: string;
  totalOffers: string;
  cohortScope: string | null;
  rank: number | null;
  fiveYearAdmissions: string;
  fiveYearHitRate: string;
  publicationDate: string | null;
  confidence: string;
  authority: string;
  note: string | null;
}

export interface OxbridgeSchool {
  rows: OxbridgeRow[];
  count: number;
  cycleFrom: number | null;
  cycleTo: number | null;
  families: string[];
  familyCounts: Record<string, number>;
  universities: string[];
  sources: SourceRef[];
}

export interface Oxbridge {
  definitions: Record<string, string>;
  families: Record<string, { key: string; label: string; summary: string; scope: string }>;
  familyOrder: string[];
  universityWide: OxbridgeRow[];
  historical: OxbridgeRow[];
  schools: Record<string, OxbridgeSchool>;
  total: number;
}

export interface UsRow {
  recordId: string;
  slug: string;
  schoolId: string | null;
  period: string;
  year: number | null;
  institution: string;
  institutionRaw: string | null;
  country: string | null;
  region: string | null;
  metricType: string;
  metricLabel: string;
  metricDefinition: string | null;
  count: string;
  aggregate: boolean;
  grain: string | null;
  denominator: string;
  denominatorBasis: string | null;
  rate: string;
  rateDenominator: string | null;
  status: string;
  canonical: boolean;
  conflictGroup: string | null;
  notes: string | null;
}

export interface UsSchool {
  rows: UsRow[];
  count: number;
  from: number | null;
  to: number | null;
  institutions: number;
  aggregates: number;
  periods: string[];
  metricTypes: string[];
  regions: string[];
  sources: SourceRef[];
}

export interface Us {
  grain: string | null;
  intendedUse: string | null;
  safeguards: string[];
  metricTypes: Record<string, string>;
  metricCounts: Record<string, number>;
  schools: Record<string, UsSchool>;
  total: number;
}

export interface Correction {
  id: string;
  rows: { label: string; href: string }[];
  schoolId: string | null;
  school: string;
  period: string;
  metric: string;
  old: string;
  new: string;
  reason: string;
  status: string;
  sources: SourceRef[];
}

export interface Conflict {
  id: string;
  schoolId: string | null;
  school: string;
  period: string;
  metric: string;
  values: { value: string; basis: string | null; source: string | null }[];
  treatment: string;
}

export interface Corrections {
  corrections: Correction[];
  conflicts: Conflict[];
  versionAuthority: { order: number; version: string; controls: string; doesNotControl: string | null }[];
}

export interface Method {
  confidenceCodes: Record<string, string>;
  definitions: Record<string, string>;
  gradeMapping: Record<string, string>;
  guardrails: string[];
  lineage: { versions: string; phase: string; effect: string }[];
  versionAuthority: Corrections['versionAuthority'];
  gradingScales: { qualification: string; label: string; denominator: string; note: string }[];
  oxbridgeDefinitions: Record<string, string>;
  usSafeguards: string[];
  sourceReferences: number;
}

export interface EvidenceRecord {
  id: string;
  slug: string;
  corpus: 'figures' | 'granular' | 'oxbridge' | 'us';
  corpusLabel: string;
  schoolId: string | null;
  school: string;
  year: number | null;
  period: string;
  domain: string;
  outcome: string;
  title: string;
  status: string;
  statusFamily: string;
  summary: { label: string; value: string }[];
  detail: { label: string; value: string }[];
  sources: SourceRef[];
  route: string;
  datasetId: string | null;
  derived: boolean;
  conflictGroup: string | null;
  canonical: boolean | null;
}

export interface SearchEntry {
  id: string;
  c: string;
  sc: string | null;
  y: number | null;
  p: string;
  d: string;
  o: string;
  t: string;
  st: string;
  f: string;
  v: string[];
  q: string;
  ds: string | null;
}

export interface SourceRegisterEntry extends SourceRef {
  key: string;
  id: string | null;
  linkedDatasets: string[];
  domains: string[];
  schools: string[];
}
