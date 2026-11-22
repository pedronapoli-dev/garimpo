import createClient from 'openapi-fetch';

import { signInAs, signOutForTest } from '@/test-utils/session';
import { useSession } from '@/stores/session';

import { authMiddleware } from './client';
import type { paths } from './schema';

/**
 * On a device, fetch comes from Expo and its response is not an instance of
 * the global Response class, which Jest's fetch would hide.
 */
class NativeLikeResponse {
  readonly headers = new Headers({ 'Content-Type': 'application/json', 'Content-Length': '19' });
  readonly body = null;
  readonly ok: boolean;

  constructor(
    readonly status: number,
    private readonly payload: unknown,
  ) {
    this.ok = status < 400;
  }

  async json() {
    return this.payload;
  }

  async text() {
    return JSON.stringify(this.payload);
  }
}

function clientReturning(response: NativeLikeResponse) {
  const api = createClient<paths>({
    baseUrl: 'http://api.test',
    fetch: (async () => response) as unknown as typeof fetch,
  });
  api.use(authMiddleware);
  return api;
}

afterEach(signOutForTest);

it("reads a response from Expo's fetch", async () => {
  const api = clientReturning(new NativeLikeResponse(200, { status: 'ok' }));

  const { data } = await api.GET('/health');

  expect(data).toEqual({ status: 'ok' });
});

it("signs out on a 401 from Expo's fetch", async () => {
  signInAs();
  const api = clientReturning(
    new NativeLikeResponse(401, { code: 'not_authenticated', message: 'No.' }),
  );

  await api.GET('/health');

  expect(useSession.getState().token).toBeNull();
});
