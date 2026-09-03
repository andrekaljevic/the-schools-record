/**
 * Form submissions: a pure `Request → Response` handler that any runtime can host
 * (Cloudflare Pages Functions here; a Node or Deno server elsewhere).
 *
 * Every response tells the truth about what happened to the submission:
 *   forwarded — a configured HTTPS review endpoint confirmed receipt (durable);
 *   failed    — nothing durable received it, and the submitter is told to keep a copy.
 * There is no "stored locally" state on a static host: without a confirmed
 * receiver the handler never claims the submission was kept.
 *
 * Abuse controls: a honeypot field, a minimum fill time, field length limits and
 * a per-client rate limit (in-memory here; a platform KV store can replace it).
 */

export type Kind = 'professional-enquiry' | 'correction-report';

export interface Env {
  REVIEW_WEBHOOK_URL?: string;
  REVIEW_WEBHOOK_TOKEN?: string;
}

export interface Receipt {
  status: 'forwarded' | 'failed';
  reference: string;
  detail: string;
  durable: boolean;
  fields: Record<string, string>;
}

const FIELDS: Record<Kind, { required: string[]; optional: string[]; max: Record<string, number> }> = {
  'professional-enquiry': {
    required: ['name', 'email', 'role', 'schools', 'deliverable', 'intendedUse', 'consent'],
    optional: ['organisation', 'deadline', 'budgetBand'],
    max: { name: 120, email: 254, role: 60, organisation: 160, schools: 500, deliverable: 60, deadline: 80, budgetBand: 40, intendedUse: 2000 },
  },
  'correction-report': {
    required: ['name', 'email', 'school', 'issue', 'consent'],
    optional: ['period', 'dataset', 'evidenceReference'],
    max: { name: 120, email: 254, school: 120, period: 80, dataset: 160, issue: 4000, evidenceReference: 1000 },
  },
};

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_FILL_MS = 2500;
const RATE_LIMIT = { window: 10 * 60 * 1000, max: 5 };
const seen = new Map<string, number[]>();

export function reference(kind: Kind, now: Date): string {
  const stamp = now.toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, '').replace('T', '-');
  return `${kind.slice(0, 3).toUpperCase()}-${stamp}`;
}

/**
 * A per-client window kept in memory.  On a serverless host each isolate keeps its own
 * map, so this is a first line only; a shared store (KV, Durable Object) or a challenge
 * belongs in front of it for production traffic.  Stale keys are evicted on every call.
 */
function rateLimited(key: string | null, now: number): boolean {
  for (const [other, times] of seen) {
    const live = times.filter((time) => now - time < RATE_LIMIT.window);
    if (live.length === 0) seen.delete(other);
    else seen.set(other, live);
  }
  if (key === null) return false; // an unidentifiable client is never made to share a bucket
  const recent = seen.get(key) ?? [];
  recent.push(now);
  seen.set(key, recent);
  return recent.length > RATE_LIMIT.max;
}

function clientKey(request: Request): string | null {
  return request.headers.get('cf-connecting-ip') ?? request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? null;
}

const SECURITY_HEADERS = {
  'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
  'strict-transport-security': 'max-age=63072000; includeSubDomains; preload',
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY',
  'referrer-policy': 'strict-origin-when-cross-origin',
  'cache-control': 'no-store',
};

async function readFields(request: Request): Promise<Record<string, string>> {
  const type = request.headers.get('content-type') ?? '';
  if (type.includes('application/json')) {
    const body = (await request.json()) as Record<string, unknown>;
    return Object.fromEntries(Object.entries(body).map(([key, value]) => [key, typeof value === 'boolean' ? (value ? 'on' : '') : String(value ?? '')]));
  }
  const form = await request.formData();
  const out: Record<string, string> = {};
  form.forEach((value, key) => { out[key] = typeof value === 'string' ? value : ''; });
  return out;
}

export function validate(kind: Kind, raw: Record<string, string>): { fields: Record<string, string>; errors: Record<string, string> } {
  const spec = FIELDS[kind];
  const errors: Record<string, string> = {};
  const fields: Record<string, string> = {};
  for (const key of [...spec.required, ...spec.optional]) {
    const value = (raw[key] ?? '').toString().trim();
    const limit = spec.max[key];
    if (limit && value.length > limit) errors[key] = `Please keep this under ${limit} characters.`;
    if (spec.required.includes(key) && value === '') errors[key] = 'This field is required.';
    if (key === 'consent' && value !== 'on' && value !== 'true') errors[key] = 'Please confirm the privacy notice.';
    if (key !== 'consent') fields[key] = value;
  }
  if (fields.email && !EMAIL.test(fields.email)) errors.email = 'Please give a valid email address.';
  return { fields, errors };
}

export function transcript(fields: Record<string, string>): string {
  return Object.entries(fields).filter(([, value]) => value !== '').map(([key, value]) => `${key}: ${value}`).join('\n');
}

async function forward(env: Env, payload: Record<string, unknown>, fetcher: typeof fetch): Promise<boolean> {
  const url = env.REVIEW_WEBHOOK_URL;
  if (!url || !url.toLowerCase().startsWith('https://')) return false;
  try {
    const response = await fetcher(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json; charset=utf-8', ...(env.REVIEW_WEBHOOK_TOKEN ? { authorization: `Bearer ${env.REVIEW_WEBHOOK_TOKEN}` } : {}) },
      body: JSON.stringify(payload),
    });
    return response.ok;
  } catch {
    return false;
  }
}

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8', ...SECURITY_HEADERS } });
}

export async function handle(kind: Kind, request: Request, env: Env, options: { now?: () => Date; fetcher?: typeof fetch } = {}): Promise<Response> {
  const now = options.now ?? (() => new Date());
  const fetcher = options.fetcher ?? fetch;
  if (request.method !== 'POST') return json({ error: 'Method not allowed' }, 405);
  const wantsJson = (request.headers.get('accept') ?? '').includes('application/json');
  const raw = await readFields(request).catch(() => ({}) as Record<string, string>);

  // Bots fill the hidden field or submit instantly; both are dropped without a receipt.
  if (raw.website && raw.website.trim() !== '') return json({ error: 'Rejected' }, 422);
  const started = Number(raw.started ?? 0);
  if (Number.isFinite(started) && started > 0 && now().getTime() - started < MIN_FILL_MS) return json({ error: 'Rejected' }, 422);
  if (rateLimited(clientKey(request), now().getTime())) return json({ error: 'Too many submissions. Please try again later.' }, 429);

  const { fields, errors } = validate(kind, raw);
  if (Object.keys(errors).length > 0) return json({ error: 'Please complete every required field.', errors }, 400);

  const received = now();
  const ref = reference(kind, received);
  const payload = { kind, reference: ref, received: received.toISOString(), ...fields };
  const forwarded = await forward(env, payload, fetcher);
  const receipt: Receipt = forwarded
    ? { status: 'forwarded', reference: ref, detail: 'Forwarded to the configured review endpoint, which confirmed receipt.', durable: true, fields }
    : { status: 'failed', reference: ref, detail: 'No review endpoint confirmed receipt of this submission, so it has not been stored. Please keep the copy below and send it by another route.', durable: false, fields };
  if (wantsJson) return json(receipt, forwarded ? 200 : 503);
  return new Response(receiptHtml(kind, receipt), { status: forwarded ? 200 : 503, headers: { 'content-type': 'text/html; charset=utf-8', ...SECURITY_HEADERS } });
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' })[char] ?? char);
}

/** Plain receipt for submissions made without JavaScript. */
export function receiptHtml(kind: Kind, receipt: Receipt): string {
  const label = kind === 'correction-report' ? 'Report' : 'Enquiry';
  const heading = receipt.status === 'forwarded' ? `${label} received for review.` : `${label} not recorded.`;
  return `<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(heading)} | The Schools Record</title><meta name="robots" content="noindex"><style>body{font-family:Georgia,serif;max-width:40rem;margin:3rem auto;padding:0 1rem;color:#172322;background:#f3f0e8}pre{white-space:pre-wrap;background:#fff;border:1px solid #c9c0b0;padding:1rem}</style></head><body><h1>${escapeHtml(heading)}</h1><p>${escapeHtml(receipt.detail)} Reference <code>${escapeHtml(receipt.reference)}</code>.</p><p>No payment has been taken and no automated email has been sent.</p><h2>Copy of your submission</h2><pre>${escapeHtml(transcript(receipt.fields))}</pre><p><a href="/">Return to The Schools Record</a></p></body></html>`;
}
