import { makePage } from '@/test-utils/fixtures';

import { mergePages } from './cache';

describe('mergePages', () => {
  it('returns an empty list for no pages', () => {
    expect(mergePages([])).toEqual([]);
  });

  it('concatenates pages in order', () => {
    const merged = mergePages([makePage([5, 4], 'c1'), makePage([3, 2])]);

    expect(merged.map((item) => item.id)).toEqual([5, 4, 3, 2]);
  });

  it('keeps the first occurrence of a repeated recommendation', () => {
    const merged = mergePages([makePage([5, 4], 'c1'), makePage([4, 3])]);

    expect(merged.map((item) => item.id)).toEqual([5, 4, 3]);
  });
});
