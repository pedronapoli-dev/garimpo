import type { ReactNode } from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';
import { fetch } from 'expo/fetch';

import { client } from '@/api/client';
import { CreateScreen } from '@/features/recommendations/components/create-screen';
import { createTestQueryClient, ok, queryWrapper } from '@/test-utils/query';
import { signInAs } from '@/test-utils/session';

import type { AssistEvent } from '../types';

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
  useRouter: () => ({ push: jest.fn() }),
}));
jest.mock('@/api/client', () => ({ API_URL: 'http://api.test', client: { GET: jest.fn() } }));
jest.mock('expo/fetch', () => ({ fetch: jest.fn() }));

const GET = client.GET as jest.Mock;
const FETCH = fetch as jest.Mock;

function streamOf(events: AssistEvent[]) {
  const chunks = events.map((event) =>
    new TextEncoder().encode(`data: ${JSON.stringify(event)}\n\n`),
  );
  return {
    ok: true,
    status: 200,
    body: {
      getReader: () => ({
        read: async () =>
          chunks.length > 0 ? { done: false, value: chunks.shift() } : { done: true },
      }),
    },
  };
}

beforeEach(() => signInAs());
afterEach(() => jest.resetAllMocks());

async function renderWithAssist(enabled: boolean) {
  GET.mockResolvedValue(ok({ enabled }));
  await render(<CreateScreen />, { wrapper: queryWrapper(createTestQueryClient()) });
}

async function fillDraft() {
  await fireEvent.changeText(screen.getByLabelText('Artist'), 'Arthur Verocai');
  await fireEvent.changeText(screen.getByLabelText('Genres'), 'mpb');
  await fireEvent.changeText(screen.getByLabelText('Why listen'), 'Great album.');
}

it('is hidden when the server has no assist', async () => {
  await renderWithAssist(false);

  expect(await screen.findByRole('button', { name: 'Publish' })).toBeOnTheScreen();
  expect(screen.queryByRole('button', { name: 'Review my text' })).toBeNull();
});

it('waits for an artist and a text before reviewing', async () => {
  await renderWithAssist(true);

  const button = await screen.findByRole('button', { name: 'Review my text' });

  expect(button).toBeDisabled();
});

it('shows the feedback and adds a suggested genre when tapped', async () => {
  FETCH.mockResolvedValue(
    streamOf([
      { type: 'feedback_delta', text: 'Say what it ' },
      { type: 'feedback_delta', text: 'sounds like.' },
      {
        type: 'done',
        result: {
          explains_why: false,
          feedback: 'Say what it sounds like.',
          suggested_genres: ['mpb', 'jazz'],
        },
      },
    ]),
  );
  await renderWithAssist(true);
  await fillDraft();

  await fireEvent.press(await screen.findByRole('button', { name: 'Review my text' }));

  expect(await screen.findByText('Say what it sounds like.')).toBeOnTheScreen();
  expect(screen.getByText('Your text could say more about why to listen.')).toBeOnTheScreen();
  // mpb is already in the form, so only jazz is offered.
  expect(screen.queryByRole('button', { name: '+ mpb' })).toBeNull();
  await fireEvent.press(screen.getByRole('button', { name: '+ jazz' }));

  expect(screen.getByLabelText('Genres')).toHaveDisplayValue('mpb, jazz');
  expect(screen.queryByRole('button', { name: '+ jazz' })).toBeNull();
});

it('shows the error when the review fails', async () => {
  FETCH.mockResolvedValue(
    streamOf([{ type: 'error', code: 'assist_unavailable', message: 'Unavailable right now.' }]),
  );
  await renderWithAssist(true);
  await fillDraft();

  await fireEvent.press(await screen.findByRole('button', { name: 'Review my text' }));

  expect(await screen.findByText('Unavailable right now.')).toBeOnTheScreen();
});
