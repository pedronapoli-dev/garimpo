import type { InfiniteData } from '@tanstack/react-query';

import { makePage, makeRecommendation } from '@/test-utils/fixtures';

import {
  applySave,
  applyVote,
  mergePages,
  rollbackVote,
  setVoteState,
  updateInPages,
} from './cache';
import type { RecommendationPage } from './types';

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

describe('applyVote', () => {
  it('adds a vote', () => {
    const voted = applyVote(makeRecommendation({ vote_count: 2 }), true);

    expect(voted).toMatchObject({ vote_count: 3, voted_by_me: true });
  });

  it('removes a vote', () => {
    const recommendation = makeRecommendation({ vote_count: 3, voted_by_me: true });

    expect(applyVote(recommendation, false)).toMatchObject({ vote_count: 2, voted_by_me: false });
  });

  it('returns the same object when the state does not change', () => {
    const recommendation = makeRecommendation({ vote_count: 3, voted_by_me: true });

    expect(applyVote(recommendation, true)).toBe(recommendation);
  });

  it('never counts below zero', () => {
    const recommendation = makeRecommendation({ vote_count: 0, voted_by_me: true });

    expect(applyVote(recommendation, false).vote_count).toBe(0);
  });
});

describe('rollbackVote and setVoteState', () => {
  it('restores the state from before the optimistic update', () => {
    const before = makeRecommendation({ vote_count: 2, voted_by_me: false });
    const optimistic = applyVote(before, true);

    expect(rollbackVote(optimistic, before)).toMatchObject({ vote_count: 2, voted_by_me: false });
  });

  it('takes the server state as the truth', () => {
    const optimistic = makeRecommendation({ vote_count: 3, voted_by_me: true });

    expect(setVoteState(optimistic, { vote_count: 7, voted_by_me: true }).vote_count).toBe(7);
  });
});

describe('applySave', () => {
  it('sets the saved flag', () => {
    expect(applySave(makeRecommendation(), true).saved_by_me).toBe(true);
  });
});

describe('updateInPages', () => {
  const data: InfiniteData<RecommendationPage, string | null> = {
    pages: [makePage([3, 2], 'c1'), makePage([1])],
    pageParams: [null, 'c1'],
  };

  it('updates the matching recommendation in any page', () => {
    const updated = updateInPages(data, 1, (item) => applyVote(item, true));

    expect(updated?.pages[1].items[0]).toMatchObject({ id: 1, vote_count: 1 });
    expect(updated?.pages[0]).toBe(data.pages[0]);
  });

  it('returns the same data when the recommendation is not cached', () => {
    expect(updateInPages(data, 99, (item) => applyVote(item, true))).toBe(data);
  });

  it('passes undefined through', () => {
    expect(updateInPages(undefined, 1, (item) => item)).toBeUndefined();
  });
});
