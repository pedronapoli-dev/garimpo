import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { client } from '@/api/client';
import { makeRecommendation } from '@/test-utils/fixtures';
import { createTestQueryClient, ok, queryWrapper } from '@/test-utils/query';
import { CURATOR, signInAs, signOutForTest } from '@/test-utils/session';

import { VoteButton } from './vote-button';

const mockPush = jest.fn();

jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush }) }));
jest.mock('@/api/client', () => ({ client: { PUT: jest.fn(), DELETE: jest.fn() } }));

const PUT = client.PUT as jest.Mock;

afterEach(() => jest.resetAllMocks());

const othersRecommendation = makeRecommendation({
  id: 3,
  vote_count: 4,
  author: { id: 99, display_name: 'Other' },
});

async function renderButton(recommendation = othersRecommendation) {
  await render(<VoteButton recommendation={recommendation} />, {
    wrapper: queryWrapper(createTestQueryClient()),
  });
}

it('sends a signed-out user to log in', async () => {
  signOutForTest();
  await renderButton();

  await fireEvent.press(screen.getByRole('button', { name: 'Vote, 4 votes' }));

  expect(mockPush).toHaveBeenCalledWith('/account/login');
  expect(PUT).not.toHaveBeenCalled();
});

it('votes for a signed-in user', async () => {
  signInAs(CURATOR);
  PUT.mockResolvedValue(ok({ vote_count: 5, voted_by_me: true }));
  await renderButton();

  await fireEvent.press(screen.getByRole('button', { name: 'Vote, 4 votes' }));

  await waitFor(() =>
    expect(PUT).toHaveBeenCalledWith('/recommendations/{recommendation_id}/vote', {
      params: { path: { recommendation_id: 3 } },
    }),
  );
});

it('is disabled on your own recommendation (rule 4)', async () => {
  signInAs(CURATOR);
  await renderButton(makeRecommendation({ author: { id: CURATOR.id, display_name: 'Pedro' } }));

  expect(screen.getByRole('button', { name: 'Vote, 0 votes' })).toBeDisabled();
});
