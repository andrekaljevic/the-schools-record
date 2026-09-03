import { describe, expect, it } from 'vitest';
import { esc, plural, slugify } from '../../src/lib/html';
import { toFixed, formatPoint, clampInt } from '../../src/lib/format';

describe('helpers', () => {
  it('escapes HTML', () => {
    expect(esc('<a href="x">&\'')).toBe('&lt;a href=&quot;x&quot;&gt;&amp;&#x27;');
  });
  it('slugifies periods the way the Python layer does', () => {
    expect(slugify('2016')).toBe('2016');
    expect(slugify('2020/21 entry')).toBe('2020-21-entry');
    expect(slugify('')).toBe('row');
  });
  it('pluralises', () => {
    expect(plural(1, 'record')).toBe('record');
    expect(plural(2, 'record')).toBe('records');
    expect(plural(0, 'reference')).toBe('references');
  });
  it('formats values like the published site', () => {
    expect(toFixed(47.85)).toBe('47.9');
    expect(toFixed(52.25)).toBe('52.3');
    expect(formatPoint(12.345, 'percent')).toBe('12.3%');
    expect(formatPoint(1234, 'count')).toBe('1,234');
    expect(clampInt('2030', 2000, 2026, 2000)).toBe(2026);
    expect(clampInt('abc', 2000, 2026, 2005)).toBe(2005);
  });
});
