import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import type { ReactNode } from 'react';

import { client } from '@/api/client';
import { useSession } from '@/stores/session';
import { createTestQueryClient, failure, ok, queryWrapper } from '@/test-utils/query';
import { CURATOR, signOutForTest } from '@/test-utils/session';

import { LoginScreen } from './login-screen';

const mockDismissTo = jest.fn();

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) => children,
  useRouter: () => ({ dismissTo: mockDismissTo }),
}));
jest.mock('@/api/client', () => ({ client: { POST: jest.fn() } }));

const POST = client.POST as jest.Mock;

beforeEach(() => signOutForTest());
afterEach(() => jest.resetAllMocks());

async function logIn(email: string, password: string) {
  await render(<LoginScreen />, { wrapper: queryWrapper(createTestQueryClient()) });
  await fireEvent.changeText(screen.getByLabelText('Email'), email);
  await fireEvent.changeText(screen.getByLabelText('Password'), password);
  await fireEvent.press(screen.getByRole('button', { name: 'Log in' }));
}

it('signs in and returns to the account tab', async () => {
  POST.mockResolvedValue(ok({ access_token: 'jwt', token_type: 'bearer', user: CURATOR }));

  await logIn(' pedro@example.com ', 'a long password');

  await waitFor(() => expect(mockDismissTo).toHaveBeenCalledWith('/account'));
  expect(useSession.getState()).toMatchObject({ status: 'signedIn', token: 'jwt' });
  expect(POST).toHaveBeenCalledWith('/auth/login', {
    body: { email: 'pedro@example.com', password: 'a long password' },
  });
});

it('shows the API message for wrong credentials', async () => {
  POST.mockResolvedValue(
    failure(401, { code: 'invalid_credentials', message: 'Wrong email or password.' }),
  );

  await logIn('pedro@example.com', 'wrong');

  expect(await screen.findByText('Wrong email or password.')).toBeOnTheScreen();
  expect(useSession.getState().status).toBe('signedOut');
});

it('validates the email before calling the API', async () => {
  await logIn('pedro', 'x');

  expect(screen.getByText('Enter a valid email.')).toBeOnTheScreen();
  expect(POST).not.toHaveBeenCalled();
});
