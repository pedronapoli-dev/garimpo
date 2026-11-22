import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

/**
 * A fresh QueryClient per test:
 * - no retries, so failures surface at once;
 * - no garbage-collection timers, which would keep Jest running after the test;
 * - notifyOnChangeProps 'all': by default a hook re-renders only for the result
 *   fields read during render, and renderHook tests read them afterwards.
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity, notifyOnChangeProps: 'all' },
      mutations: { retry: false, gcTime: Infinity },
    },
  });
}

export function queryWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

/** The shape openapi-fetch resolves with, for mocking `client.GET` and friends. */
export function ok<T>(data: T, status = 200) {
  return { data, response: { ok: true, status } as Response };
}

export function failure(status: number, error: unknown) {
  return { error, response: { ok: false, status } as Response };
}
