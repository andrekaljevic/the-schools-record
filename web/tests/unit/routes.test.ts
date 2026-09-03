import { describe, expect, it } from 'vitest';
import { legacyTarget, recordPath, claimPath } from '../../src/lib/routes';

describe('legacy Streamlit links map to canonical pages', () => {
  it.each([
    ['?p=/', '/'],
    ['?p=/schools', '/schools/'],
    ['?p=/schools/winchester/exam-results', '/schools/winchester/exam-results/'],
    ['?p=/schools&series=gcse_grade_9', '/schools/series/gcse-grade-9/'],
    ['?p=/schools&series=public-source-b6f5e1ed22afa0a6', '/schools/series/oxbridge-destinations/'],
    ['?p=/schools&series=a_level_astar', '/schools/'],
    ['?p=/evidence&record=ox:oxford-apply-centre-2006-10092', '/evidence/records/ox/oxford-apply-centre-2006-10092/'],
    ['?p=/evidence&section=sources', '/evidence/sources/'],
    ['?p=/evidence&section=method', '/evidence/method/'],
    ['?p=/evidence&school=eton&q=oxford', '/evidence/?school=eton&q=oxford'],
    ['?p=/evidence&school=Winchester+College&dataset=winchester_gcse&period=2016', '/evidence/?school=Winchester+College&dataset=winchester_gcse&period=2016'],
    ['?p=/compare&schools=eton,westminster&metric=a_level_astar&from=2010&to=2019', '/compare/?schools=eton%2Cwestminster&metric=a_level_astar&from=2010&to=2019'],
    ['?p=/corrections&school=winchester', '/corrections/schools/winchester/'],
    ['?p=/corrections/report', '/corrections/report/'],
  ])('%s → %s', (search, expected) => {
    expect(legacyTarget(search)).toBe(expected);
  });

  it('ignores links that are not legacy routes', () => {
    expect(legacyTarget('')).toBeNull();
    expect(legacyTarget('?q=eton')).toBeNull();
    expect(legacyTarget('?p=https://example.com')).toBeNull();
  });

  it('builds record and claim paths', () => {
    expect(recordPath('fig:winchester_gcse:3')).toBe('/evidence/records/fig/winchester_gcse/3/');
    expect(claimPath('winchester_gcse', '2016')).toBe('/evidence/?dataset=winchester_gcse&period=2016');
  });
});
