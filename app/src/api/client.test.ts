import type { MiddlewareCallbackParams } from 'openapi-fetch';

import { useSession } from '@/stores/session';

import { authMiddleware } from './client';

const user = { id: 2, email: 'pedro@example.com', display_name: 'Pedro' };

function params(request: Request): MiddlewareCallbackParams {
  return { request } as MiddlewareCallbackParams;
}

async function onRequest(request: Request): Promise<Request> {
  return (await authMiddleware.onRequest!(params(request))) as Request;
}

async function onResponse(request: Request, status: number): Promise<void> {
  await authMiddleware.onResponse!({
    ...params(request),
    response: new Response(null, { status }),
  });
}

beforeEach(() => useSession.setState({ status: 'signedOut', token: null, user: null }));

it('adds the bearer token when signed in', async () => {
  useSession.setState({ status: 'signedIn', token: 'jwt', user });

  const request = await onRequest(new Request('http://api/invites'));

  expect(request.headers.get('Authorization')).toBe('Bearer jwt');
});

it('sends no token when signed out', async () => {
  const request = await onRequest(new Request('http://api/recommendations'));

  expect(request.headers.has('Authorization')).toBe(false);
});

it('signs out on a 401 for a request that carried a token', async () => {
  useSession.setState({ status: 'signedIn', token: 'expired', user });
  const request = await onRequest(new Request('http://api/invites'));

  await onResponse(request, 401);

  expect(useSession.getState().status).toBe('signedOut');
});

it('ignores a 401 without a token, such as a wrong password', async () => {
  useSession.setState({ status: 'signedIn', token: 'jwt', user });

  await onResponse(new Request('http://api/auth/login'), 401);

  expect(useSession.getState().status).toBe('signedIn');
});
