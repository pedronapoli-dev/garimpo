import type { Recommendation } from './types';

/** "Arthur Verocai — Arthur Verocai" for albums and tracks, just the artist otherwise. */
export function headline(recommendation: Pick<Recommendation, 'artist' | 'title'>): string {
  return recommendation.title
    ? `${recommendation.artist} — ${recommendation.title}`
    : recommendation.artist;
}

export const TYPE_LABELS: Record<Recommendation['type'], string> = {
  artist: 'Artist',
  album: 'Album',
  track: 'Track',
};

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
