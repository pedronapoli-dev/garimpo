import type { Recommendation, RecommendationPage } from './types';

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
