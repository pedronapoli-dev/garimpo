import { render, screen } from '@testing-library/react-native';

import { client } from '@/api/client';
import { makeRecommendation } from '@/test-utils/fixtures';
import { createTestQueryClient, ok, queryWrapper } from '@/test-utils/query';
import { CURATOR, signInAs, signOutForTest } from '@/test-utils/session';

import { DetailScreen } from './detail-screen';

jest.mock('expo-router', () => ({
  Stack: { Screen: () => null },
  useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
}));
jest.mock('@/api/client', () => ({ client: { GET: jest.fn() } }));

const GET = client.GET as jest.Mock;

beforeEach(() => {
  GET.mockResolvedValue(
    ok(makeRecommendation({ id: 4, author: { id: 1, display_name: 'Pedro' } })),
  );
});
afterEach(() => jest.resetAllMocks());

async function renderScreen() {
  await render(<DetailScreen id={4} />, { wrapper: queryWrapper(createTestQueryClient()) });
  await screen.findByText('Why listen');
}

it('shows edit and delete to the author', async () => {
  signInAs(CURATOR);
  await renderScreen();

  expect(screen.getByRole('button', { name: 'Edit' })).toBeOnTheScreen();
  expect(screen.getByRole('button', { name: 'Delete' })).toBeOnTheScreen();
});

it('hides edit and delete from other users', async () => {
  signInAs({ id: 2, email: 'other@example.com', display_name: 'Other' });
  await renderScreen();

  expect(screen.queryByRole('button', { name: 'Edit' })).toBeNull();
});

it('hides edit and delete when signed out', async () => {
  signOutForTest();
  await renderScreen();

  expect(screen.queryByRole('button', { name: 'Delete' })).toBeNull();
});
