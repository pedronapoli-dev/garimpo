import type { Recommendation, RecommendationCreate, RecommendationType } from './types';

// The API enforces these rules (rule 2). The app repeats them only to give
// feedback while typing; it still handles the API's 422 responses.
export const TEXT_MIN = 80;
export const TEXT_MAX = 1000;
export const GENRES_MIN = 1;
export const GENRES_MAX = 5;

/** Form state: every field is the raw text the user typed. */
export type RecommendationForm = {
  type: RecommendationType;
  artist: string;
  title: string;
  genres: string;
  text: string;
};

export type FormErrors = Partial<Record<keyof RecommendationForm, string>>;

export function emptyForm(): RecommendationForm {
  return { type: 'album', artist: '', title: '', genres: '', text: '' };
}

/** Pre-fills the edit form with a stored recommendation. */
export function formFromRecommendation(recommendation: Recommendation): RecommendationForm {
  return {
    type: recommendation.type,
    artist: recommendation.artist,
    title: recommendation.title ?? '',
    genres: recommendation.genres.join(', '),
    text: recommendation.text,
  };
}

/** "MPB, Hip  Hop, mpb" -> ["mpb", "hip hop"], the same normalization as the API. */
export function parseGenres(input: string): string[] {
  const names = input
    .split(',')
    .map((name) => name.trim().split(/\s+/).join(' ').toLowerCase())
    .filter((name) => name.length > 0);
  return [...new Set(names)];
}

export function validateForm(form: RecommendationForm): FormErrors {
  const errors: FormErrors = {};
  const title = form.title.trim();

  if (form.artist.trim().length === 0) {
    errors.artist = 'Enter the artist.';
  }
  if (form.type === 'artist' && title.length > 0) {
    errors.title = 'An artist recommendation has no title.';
  }
  if (form.type !== 'artist' && title.length === 0) {
    errors.title = `Enter the ${form.type} title.`;
  }

  const genres = parseGenres(form.genres);
  if (genres.length < GENRES_MIN || genres.length > GENRES_MAX) {
    errors.genres = `Add ${GENRES_MIN} to ${GENRES_MAX} genres, separated by commas.`;
  }

  const length = form.text.trim().length;
  if (length < TEXT_MIN || length > TEXT_MAX) {
    errors.text = `Explain why to listen in ${TEXT_MIN} to ${TEXT_MAX} characters.`;
  }
  return errors;
}

export function textCounter(text: string): { label: string; valid: boolean } {
  const length = text.trim().length;
  if (length < TEXT_MIN) {
    return { label: `${length} / ${TEXT_MIN} minimum`, valid: false };
  }
  return { label: `${length} / ${TEXT_MAX}`, valid: length <= TEXT_MAX };
}

export function toCreatePayload(form: RecommendationForm): RecommendationCreate {
  const title = form.title.trim();
  return {
    type: form.type,
    artist: form.artist.trim(),
    title: form.type === 'artist' || title.length === 0 ? null : title,
    genres: parseGenres(form.genres),
    text: form.text.trim(),
  };
}

/** Adds suggested genres to the typed ones, skipping repeats, up to GENRES_MAX. */
export function addGenres(form: RecommendationForm, genres: readonly string[]): RecommendationForm {
  const merged = parseGenres([form.genres, ...genres].join(','));
  return { ...form, genres: merged.slice(0, GENRES_MAX).join(', ') };
}
