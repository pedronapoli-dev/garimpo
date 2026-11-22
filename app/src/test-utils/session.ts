import { useSession } from '@/stores/session';

export const CURATOR = { id: 1, email: 'pedro@example.com', display_name: 'Pedro' };

export function signInAs(user = CURATOR): void {
  useSession.setState({ status: 'signedIn', token: 'test-token', user });
}

export function signOutForTest(): void {
  useSession.setState({ status: 'signedOut', token: null, user: null });
}
