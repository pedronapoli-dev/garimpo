import { headline } from './format';

describe('headline', () => {
  it('joins artist and title', () => {
    expect(headline({ artist: 'Azymuth', title: 'Light As A Feather' })).toBe(
      'Azymuth — Light As A Feather',
    );
  });

  it('shows only the artist when there is no title', () => {
    expect(headline({ artist: 'Azymuth', title: null })).toBe('Azymuth');
  });
});
