import * as SecureStore from 'expo-secure-store';
import { create } from 'zustand';

import type { components } from '@/api/schema';

export type CurrentUser = components['schemas']['CurrentUserOut'];
export type SessionOut = components['schemas']['SessionOut'];

const STORAGE_KEY = 'garimpo.session';

type Persisted = { token: string; user: CurrentUser };

type SessionState = {
  /** 'restoring' until the Keychain has been read at launch. */
  status: 'restoring' | 'signedOut' | 'signedIn';
  token: string | null;
  user: CurrentUser | null;
  restore: () => Promise<void>;
  signIn: (session: SessionOut) => Promise<void>;
  signOut: () => Promise<void>;
};

/**
 * Only the token and the current user live here; server data stays in the
 * TanStack Query cache. SecureStore is the Keychain on iOS.
 */
export const useSession = create<SessionState>()((set) => ({
  status: 'restoring',
  token: null,
  user: null,

  restore: async () => {
    const persisted = parse(await SecureStore.getItemAsync(STORAGE_KEY));
    set(
      persisted
        ? { status: 'signedIn', token: persisted.token, user: persisted.user }
        : { status: 'signedOut', token: null, user: null },
    );
  },

  signIn: async ({ access_token, user }) => {
    const persisted: Persisted = { token: access_token, user };
    await SecureStore.setItemAsync(STORAGE_KEY, JSON.stringify(persisted));
    set({ status: 'signedIn', token: access_token, user });
  },

  signOut: async () => {
    await SecureStore.deleteItemAsync(STORAGE_KEY);
    set({ status: 'signedOut', token: null, user: null });
  },
}));

function parse(raw: string | null): Persisted | null {
  if (raw === null) return null;
  try {
    const value = JSON.parse(raw) as Partial<Persisted>;
    return typeof value.token === 'string' && value.user ? (value as Persisted) : null;
  } catch {
    return null;
  }
}
