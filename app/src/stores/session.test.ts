import * as SecureStore from 'expo-secure-store';

import { useSession } from './session';

const user = { id: 2, email: 'pedro@example.com', display_name: 'Pedro' };

beforeEach(async () => {
  await useSession.getState().signOut();
  useSession.setState({ status: 'restoring' });
});

it('starts restoring and ends signed out with nothing stored', async () => {
  expect(useSession.getState().status).toBe('restoring');

  await useSession.getState().restore();

  expect(useSession.getState()).toMatchObject({ status: 'signedOut', token: null, user: null });
});

it('persists the session on sign in and restores it on the next launch', async () => {
  await useSession.getState().signIn({ access_token: 'jwt', token_type: 'bearer', user });
  useSession.setState({ status: 'restoring', token: null, user: null });

  await useSession.getState().restore();

  expect(useSession.getState()).toMatchObject({ status: 'signedIn', token: 'jwt', user });
});

it('clears the stored session on sign out', async () => {
  await useSession.getState().signIn({ access_token: 'jwt', token_type: 'bearer', user });

  await useSession.getState().signOut();
  await useSession.getState().restore();

  expect(useSession.getState().status).toBe('signedOut');
});

it('treats a corrupt stored value as signed out', async () => {
  await SecureStore.setItemAsync('garimpo.session', '{not json');

  await useSession.getState().restore();

  expect(useSession.getState().status).toBe('signedOut');
});
