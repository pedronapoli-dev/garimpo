import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { client } from '@/api/client';
import { VALID_TEXT, makeRecommendation } from '@/test-utils/fixtures';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';
import { signInAs, signOutForTest } from '@/test-utils/session';

import { CreateScreen } from './create-screen';

const mockPush = jest.fn();

jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush }) }));
jest.mock('@/api/client', () => ({ client: { POST: jest.fn() } }));

const POST = client.POST as jest.Mock;

beforeEach(() => signInAs());
afterEach(() => jest.resetAllMocks());

function renderScreen() {
  return render(<CreateScreen />, { wrapper: queryWrapper(createTestQueryClient()) });
}

async function fillValidAlbum() {
  await fireEvent.changeText(screen.getByLabelText('Artist'), 'Arthur Verocai');
  await fireEvent.changeText(screen.getByLabelText('Album title'), 'Arthur Verocai');
  await fireEvent.changeText(screen.getByLabelText('Genres'), 'MPB, jazz');
  await fireEvent.changeText(screen.getByLabelText('Why listen'), VALID_TEXT);
}

it('shows field errors on submit and does not call the API', async () => {
  await renderScreen();

  await fireEvent.press(screen.getByRole('button', { name: 'Publish' }));

  expect(screen.getByText('Enter the artist.')).toBeOnTheScreen();
  expect(screen.getByText('Add 1 to 5 genres, separated by commas.')).toBeOnTheScreen();
  expect(POST).not.toHaveBeenCalled();
});

it('hides the title field for an artist recommendation', async () => {
  await renderScreen();

  await fireEvent.press(screen.getByRole('button', { name: 'Artist' }));

  expect(screen.queryByLabelText('Album title')).toBeNull();
});

it('publishes and opens the new recommendation', async () => {
  POST.mockResolvedValue(ok(makeRecommendation({ id: 12 }), 201));
  await renderScreen();
  await fillValidAlbum();

  await fireEvent.press(screen.getByRole('button', { name: 'Publish' }));

  await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/recommendations/12'));
  expect(POST).toHaveBeenCalledWith('/recommendations', {
    body: {
      type: 'album',
      artist: 'Arthur Verocai',
      title: 'Arthur Verocai',
      genres: ['mpb', 'jazz'],
      text: VALID_TEXT,
    },
  });
});

it('offers the existing recommendation on a duplicate', async () => {
  POST.mockResolvedValue(
    failure(409, {
      code: 'duplicate_recommendation',
      message: 'This artist and title were already recommended.',
      existing_id: 3,
    }),
  );
  await renderScreen();
  await fillValidAlbum();

  await fireEvent.press(screen.getByRole('button', { name: 'Publish' }));
  await fireEvent.press(
    await screen.findByRole('button', { name: 'Open the existing recommendation' }),
  );

  expect(screen.getByText('This artist and title were already recommended.')).toBeOnTheScreen();
  expect(mockPush).toHaveBeenCalledWith('/recommendations/3');
});

it('asks a signed-out user to log in', async () => {
  signOutForTest();
  await renderScreen();

  expect(screen.getByText('Log in to recommend music.')).toBeOnTheScreen();
  expect(screen.queryByLabelText('Artist')).toBeNull();
});
