import { describe, expect, it } from 'vitest';
import { handle, receiptHtml, validate } from '../../functions/lib/handler';

const now = () => new Date('2026-09-02T12:00:00Z');
const valid = { name: 'A Reader', email: 'reader@example.com', school: 'Winchester College', issue: 'The 2016 GCSE A* figure looks wrong.', consent: 'on', started: String(now().getTime() - 10_000) };

function post(body: Record<string, unknown>, headers: Record<string, string> = {}): Request {
  return new Request('https://example.test/api/correction', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json', 'cf-connecting-ip': headers.ip ?? '203.0.113.1', ...headers }, body: JSON.stringify(body) });
}

describe('form handler', () => {
  it('rejects anything but POST', async () => {
    const response = await handle('correction-report', new Request('https://example.test/api/correction'), {}, { now });
    expect(response.status).toBe(405);
  });

  it('never claims receipt without a confirming endpoint', async () => {
    const response = await handle('correction-report', post(valid, { ip: '203.0.113.2' }), {}, { now });
    expect(response.status).toBe(503);
    const receipt = await response.json();
    expect(receipt.status).toBe('failed');
    expect(receipt.durable).toBe(false);
    expect(receipt.detail).toMatch(/has not been stored/);
    expect(receipt.fields.issue).toBe(valid.issue);
  });

  it('reports a forwarded submission only when the endpoint answers 2xx', async () => {
    const calls: { url: string; body: string; auth: string | null }[] = [];
    const fetcher = (async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), body: String(init?.body), auth: new Headers(init?.headers).get('authorization') });
      return new Response('ok', { status: 202 });
    }) as typeof fetch;
    const response = await handle('correction-report', post(valid, { ip: '203.0.113.3' }), { REVIEW_WEBHOOK_URL: 'https://review.example.test/hook', REVIEW_WEBHOOK_TOKEN: 'secret' }, { now, fetcher });
    expect(response.status).toBe(200);
    const receipt = await response.json();
    expect(receipt.status).toBe('forwarded');
    expect(receipt.durable).toBe(true);
    expect(receipt.reference).toBe('COR-20260902-120000');
    expect(calls[0]?.auth).toBe('Bearer secret');
    expect(JSON.parse(calls[0]?.body ?? '{}').school).toBe('Winchester College');
  });

  it('treats a non-2xx or non-HTTPS endpoint as not received', async () => {
    const fetcher = (async () => new Response('no', { status: 500 })) as typeof fetch;
    const failed = await handle('correction-report', post(valid, { ip: '203.0.113.4' }), { REVIEW_WEBHOOK_URL: 'https://review.example.test/hook' }, { now, fetcher });
    expect((await failed.json()).status).toBe('failed');
    const insecure = await handle('correction-report', post(valid, { ip: '203.0.113.5' }), { REVIEW_WEBHOOK_URL: 'http://review.example.test/hook' }, { now, fetcher });
    expect((await insecure.json()).status).toBe('failed');
  });

  it('validates required fields, email and consent', () => {
    const { errors } = validate('correction-report', { name: '', email: 'nope', school: 'x', issue: '', consent: '' });
    expect(Object.keys(errors).sort()).toEqual(['consent', 'email', 'issue', 'name']);
    expect(validate('professional-enquiry', { name: 'A', email: 'a@b.co', role: 'Researcher', schools: 'Eton', deliverable: 'Structured data', intendedUse: 'Research', consent: 'on' }).errors).toEqual({});
  });

  it('drops honeypot and instant submissions silently', async () => {
    const bot = await handle('correction-report', post({ ...valid, website: 'http://spam' }, { ip: '203.0.113.6' }), {}, { now });
    expect(bot.status).toBe(422);
    const instant = await handle('correction-report', post({ ...valid, started: String(now().getTime() - 100) }, { ip: '203.0.113.7' }), {}, { now });
    expect(instant.status).toBe(422);
  });

  it('rate-limits a client after five submissions in ten minutes', async () => {
    let last = 0;
    for (let index = 0; index < 6; index += 1) {
      last = (await handle('correction-report', post(valid, { ip: '203.0.113.99' }), {}, { now })).status;
    }
    expect(last).toBe(429);
  });

  it('returns an HTML receipt for a plain form post', async () => {
    const body = new URLSearchParams({ ...valid });
    const request = new Request('https://example.test/api/correction', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded', 'cf-connecting-ip': '203.0.113.8' }, body });
    const response = await handle('correction-report', request, {}, { now });
    expect(response.headers.get('content-type')).toContain('text/html');
    const html = await response.text();
    expect(html).toContain('Report not recorded');
    expect(html).toContain('Winchester College');
    expect(receiptHtml('professional-enquiry', { status: 'forwarded', reference: 'PRO-1', detail: 'ok', durable: true, fields: { name: '<b>' } })).toContain('&lt;b&gt;');
  });
});
