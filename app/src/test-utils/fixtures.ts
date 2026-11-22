import type { Recommendation, RecommendationPage } from '@/features/recommendations/types';

export const VALID_TEXT =
  'Why listen: Verocai wrote orchestral arrangements for this record that sound like nothing else.';

export function makeRecommendation(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    id: 1,
    type: 'album',
    artist: 'Arthur Verocai',
    title: 'Arthur Verocai',
    genres: ['mpb', 'jazz'],
    text: VALID_TEXT,
    author: { id: 1, display_name: 'Pedro' },
    created_at: '2026-11-21T12:00:00Z',
    updated_at: '2026-11-21T12:00:00Z',
    vote_count: 0,
    voted_by_me: false,
    saved_by_me: false,
    hidden: false,
    ...overrides,
  };
}

export function makePage(ids: number[], nextCursor: string | null = null): RecommendationPage {
  return {
    items: ids.map((id) => makeRecommendation({ id, title: `Album ${id}` })),
    next_cursor: nextCursor,
  };
}
