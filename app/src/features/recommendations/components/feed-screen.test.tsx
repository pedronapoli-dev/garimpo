import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import type { ReactNode } from 'react';

import { client } from '@/api/client';
import { makePage } from '@/test-utils/fixtures';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';

import { FeedScreen } from './feed-screen';

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
  useRouter: () => ({ push: jest.fn() }),
}));
jest.mock('@/api/client', () => ({ client: { GET: jest.fn() } }));

const GET = client.GET as jest.Mock;

afterEach(() => jest.resetAllMocks());

function mockApi(feed: (genre: string | undefined) => unknown) {
  GET.mockImplementation(
    async (path: string, options?: { params: { query: { genre?: string } } }) => {
      if (path === '/tags') return ok([{ id: 1, name: 'jazz' }]);
      return feed(options?.params.query.genre ?? undefined);
    },
  );
}

function renderScreen() {
  return render(<FeedScreen />, { wrapper: queryWrapper(createTestQueryClient()) });
}

it('lists recommendations', async () => {
  mockApi(() => ok(makePage([2, 1])));
  await renderScreen();

  expect(await screen.findByText('Arthur Verocai — Album 2')).toBeOnTheScreen();
  expect(screen.getByText('Arthur Verocai — Album 1')).toBeOnTheScreen();
});

it('filters by the selected genre', async () => {
  mockApi((genre) => ok(genre === 'jazz' ? makePage([5]) : makePage([2, 1])));
  await renderScreen();

  await fireEvent.press(await screen.findByRole('button', { name: 'jazz' }));

  expect(await screen.findByText('Arthur Verocai — Album 5')).toBeOnTheScreen();
  await waitFor(() => expect(screen.queryByText('Arthur Verocai — Album 2')).toBeNull());
});

it('shows an error with a retry button', async () => {
  mockApi(() => failure(500, 'Internal Server Error'));
  await renderScreen();

  expect(await screen.findByText('Could not load the feed')).toBeOnTheScreen();
  expect(screen.getByRole('button', { name: 'Try again' })).toBeOnTheScreen();
});

it('switches to the most voted sort', async () => {
  mockApi(() => ok(makePage([1])));
  await renderScreen();
  await screen.findByText('Arthur Verocai — Album 1');

  await fireEvent.press(screen.getByRole('button', { name: 'Most voted' }));

  await waitFor(() =>
    expect(GET).toHaveBeenLastCalledWith('/recommendations', {
      params: { query: { sort: 'top', genre: null, author_id: null, cursor: null } },
    }),
  );
});
