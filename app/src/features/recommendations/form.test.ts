import { VALID_TEXT } from '@/test-utils/fixtures';

import {
  type RecommendationForm,
  emptyForm,
  parseGenres,
  textCounter,
  toCreatePayload,
  validateForm,
} from './form';

function form(overrides: Partial<RecommendationForm> = {}): RecommendationForm {
  return {
    type: 'album',
    artist: 'Arthur Verocai',
    title: 'Arthur Verocai',
    genres: 'mpb, jazz',
    text: VALID_TEXT,
    ...overrides,
  };
}

describe('parseGenres', () => {
  it('splits on commas, trims, lowercases and collapses spaces', () => {
    expect(parseGenres(' MPB ,  Hip   Hop')).toEqual(['mpb', 'hip hop']);
  });

  it('drops empty entries and duplicates', () => {
    expect(parseGenres('jazz,, Jazz ,')).toEqual(['jazz']);
  });
});

describe('validateForm', () => {
  it('accepts a valid album', () => {
    expect(validateForm(form())).toEqual({});
  });

  it('requires an artist', () => {
    expect(validateForm(form({ artist: '  ' })).artist).toBeDefined();
  });

  it.each(['album', 'track'] as const)('requires a title for %s', (type) => {
    expect(validateForm(form({ type, title: ' ' })).title).toBeDefined();
  });

  it('rejects a title for an artist', () => {
    expect(validateForm(form({ type: 'artist', title: 'X' })).title).toBeDefined();
  });

  it('accepts an artist without a title', () => {
    expect(validateForm(form({ type: 'artist', title: '' }))).toEqual({});
  });

  it.each(['', ' , ', 'a, b, c, d, e, f'])('rejects genre list %j', (genres) => {
    expect(validateForm(form({ genres })).genres).toBeDefined();
  });

  it('accepts five genres', () => {
    expect(validateForm(form({ genres: 'a, b, c, d, e' }))).toEqual({});
  });

  it.each([79, 1001])('rejects a text of %i characters', (length) => {
    expect(validateForm(form({ text: 'x'.repeat(length) })).text).toBeDefined();
  });

  it('counts the text after trimming', () => {
    expect(validateForm(form({ text: `   ${'x'.repeat(79)}   ` })).text).toBeDefined();
  });
});

describe('textCounter', () => {
  it('shows how many characters are still needed', () => {
    expect(textCounter('x'.repeat(30))).toEqual({ label: '30 / 80 minimum', valid: false });
  });

  it('shows the remaining characters once valid', () => {
    expect(textCounter('x'.repeat(100))).toEqual({ label: '100 / 1000', valid: true });
  });
});

describe('toCreatePayload', () => {
  it('trims fields and parses genres', () => {
    expect(toCreatePayload(form({ artist: ' Verocai ', genres: 'MPB' }))).toEqual({
      type: 'album',
      artist: 'Verocai',
      title: 'Arthur Verocai',
      genres: ['mpb'],
      text: VALID_TEXT,
    });
  });

  it('sends a null title for an artist', () => {
    expect(toCreatePayload(form({ type: 'artist', title: '' })).title).toBeNull();
  });
});

describe('emptyForm', () => {
  it('starts as an album with empty fields', () => {
    expect(emptyForm()).toEqual({ type: 'album', artist: '', title: '', genres: '', text: '' });
  });
});
