import type { InfiniteData } from '@tanstack/react-query';

import type { Recommendation, RecommendationPage } from './types';

export type VoteState = Pick<Recommendation, 'vote_count' | 'voted_by_me'>;
export type FeedData = InfiniteData<RecommendationPage, string | null>;

/**
 * Flattens the pages of the infinite feed into one list.
 * A recommendation that appears twice (for example after a refetch while
 * scrolling) is kept only where it first appeared.
 */
export function mergePages(pages: readonly RecommendationPage[]): Recommendation[] {
  const seen = new Set<number>();
  const merged: Recommendation[] = [];
  for (const page of pages) {
    for (const item of page.items) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      merged.push(item);
    }
  }
  return merged;
}

/** The optimistic update for a vote or an unvote. */
export function applyVote(recommendation: Recommendation, voted: boolean): Recommendation {
  if (recommendation.voted_by_me === voted) return recommendation;
  const vote_count = Math.max(0, recommendation.vote_count + (voted ? 1 : -1));
  return { ...recommendation, vote_count, voted_by_me: voted };
}

/** Puts a known vote state back: the server's answer, or the one before a failure. */
export function setVoteState(recommendation: Recommendation, state: VoteState): Recommendation {
  return { ...recommendation, vote_count: state.vote_count, voted_by_me: state.voted_by_me };
}

/** Undoes applyVote with the state captured before it. */
export function rollbackVote(recommendation: Recommendation, previous: VoteState): Recommendation {
  return setVoteState(recommendation, previous);
}

export function applySave(recommendation: Recommendation, saved: boolean): Recommendation {
  return recommendation.saved_by_me === saved
    ? recommendation
    : { ...recommendation, saved_by_me: saved };
}

/**
 * Applies `update` to one recommendation inside cached infinite pages. Pages
 * that do not contain it keep their identity, so their lists do not re-render.
 */
export function updateInPages(
  data: FeedData | undefined,
  id: number,
  update: (recommendation: Recommendation) => Recommendation,
): FeedData | undefined {
  if (data === undefined) return undefined;
  let changed = false;
  const pages = data.pages.map((page) => {
    if (!page.items.some((item) => item.id === id)) return page;
    changed = true;
    return { ...page, items: page.items.map((item) => (item.id === id ? update(item) : item)) };
  });
  return changed ? { ...data, pages } : data;
}
