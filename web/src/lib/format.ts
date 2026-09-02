/**
 * Number formatting shared by the TypeScript chart and islands.
 *
 * `toFixed` mirrors tsr/format.to_fixed: JavaScript Number#toFixed(1) rounding,
 * which is what the published site used, so a value drawn client-side reads
 * exactly as the same value in a Python-rendered table.
 */

export function toFixed(value: number, digits = 1): string {
  return Number(value).toFixed(digits);
}

export function formatPoint(value: number, unit: 'percent' | 'count'): string {
  if (unit === 'percent') return `${toFixed(value)}%`;
  return new Intl.NumberFormat('en-US').format(value);
}

export function clampInt(value: unknown, low: number, high: number, fallback: number): number {
  const number = typeof value === 'number' ? value : Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(low, Math.min(high, number));
}
