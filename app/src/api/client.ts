import createClient, { type Middleware } from 'openapi-fetch';

import { useSession } from '@/stores/session';

import type { paths } from './schema';

// The iOS simulator reaches the Mac at localhost. On a device or the Android
// emulator, set EXPO_PUBLIC_API_URL in app/.env.local (for example
// http://10.0.2.2:8000 or http://<your-mac-ip>:8000).
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

/**
 * Sends the token with every request. A 401 on a request that carried one
 * means the token expired or was revoked, so the app signs out.
 */
export const authMiddleware: Middleware = {
  onRequest({ request }) {
    const { token } = useSession.getState();
    if (token !== null) request.headers.set('Authorization', `Bearer ${token}`);
    return request;
  },
  async onResponse({ request, response }) {
    if (response.status === 401 && request.headers.has('Authorization')) {
      await useSession.getState().signOut();
    }
    return response;
  },
};

export const client = createClient<paths>({ baseUrl: API_URL });
client.use(authMiddleware);
