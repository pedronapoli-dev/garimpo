import { act, renderHook, waitFor } from '@testing-library/react-native';
import { fetch } from 'expo/fetch';

import { client } from '@/api/client';
import { createTestQueryClient, ok, queryWrapper } from '@/test-utils/query';
import { signInAs, signOutForTest } from '@/test-utils/session';
import { useSession } from '@/stores/session';

import { useAssistReview, useAssistStatus } from './queries';
import type { AssistEvent, AssistIn } from './types';

jest.mock('expo/fetch', () => ({ fetch: jest.fn() }));
jest.mock('@/api/client', () => ({
  API_URL: 'http://api.test',
  client: { GET: jest.fn() },
}));

const FETCH = fetch as jest.Mock;
const GET = client.GET as jest.Mock;
const DRAFT: AssistIn = {
  type: 'album',
  artist: 'Arthur Verocai',
  title: 'Arthur',
  text: 'Great.',
  genres: [],
};
const RESULT = { explains_why: false, feedback: 'Say why.', suggested_genres: ['jazz'] };

/** A streamed response whose body yields each chunk in turn. */
function streamed(chunks: string[]) {
  const encoder = new TextEncoder();
  const queue = chunks.map((chunk) => encoder.encode(chunk));
  return {
    ok: true,
    status: 200,
    body: {
      getReader: () => ({
        read: async () =>
          queue.length > 0 ? { done: false, value: queue.shift() } : { done: true },
      }),
    },
  };
}

const frame = (event: AssistEvent) => `data: ${JSON.stringify(event)}\n\n`;

function errorResponse(status: number, body: unknown) {
  return { ok: false, status, body: null, json: async () => body };
}

beforeEach(() => signInAs());
afterEach(() => {
  jest.resetAllMocks();
  signOutForTest();
});

describe('useAssistStatus', () => {
  it('reports whether the server has an assist', async () => {
    GET.mockResolvedValue(ok({ enabled: true }));
    const { result } = await renderHook(() => useAssistStatus(), {
      wrapper: queryWrapper(createTestQueryClient()),
    });

    await waitFor(() => expect(result.current.data).toEqual({ enabled: true }));
    expect(GET).toHaveBeenCalledWith('/assist/status');
  });
});

describe('useAssistReview', () => {
  it('builds the feedback from deltas, then keeps the result', async () => {
    // The second delta is split across two network chunks.
    const second = frame({ type: 'feedback_delta', text: 'why.' });
    FETCH.mockResolvedValue(
      streamed([
        frame({ type: 'feedback_delta', text: 'Say ' }),
        second.slice(0, 12),
        second.slice(12),
        frame({ type: 'done', result: RESULT }),
      ]),
    );
    const { result } = await renderHook(() => useAssistReview());

    await act(() => result.current.start(DRAFT));

    expect(result.current.status).toBe('done');
    expect(result.current.feedback).toBe('Say why.');
    expect(result.current.result).toEqual(RESULT);
    const [url, init] = FETCH.mock.calls[0];
    expect(url).toBe('http://api.test/assist/review');
    expect(init.headers.Authorization).toBe('Bearer test-token');
    expect(JSON.parse(init.body)).toEqual(DRAFT);
  });

  it('shows the message of an error event', async () => {
    FETCH.mockResolvedValue(
      streamed([frame({ type: 'error', code: 'assist_unavailable', message: 'Later.' })]),
    );
    const { result } = await renderHook(() => useAssistReview());

    await act(() => result.current.start(DRAFT));

    expect(result.current.status).toBe('error');
    expect(result.current.error).toBe('Later.');
  });

  it('shows the message of an error response', async () => {
    FETCH.mockResolvedValue(
      errorResponse(503, { code: 'assist_disabled', message: 'Not configured.' }),
    );
    const { result } = await renderHook(() => useAssistReview());

    await act(() => result.current.start(DRAFT));

    expect(result.current.error).toBe('Not configured.');
  });

  it('signs out when the token is rejected', async () => {
    FETCH.mockResolvedValue(errorResponse(401, { code: 'not_authenticated', message: 'No.' }));
    const { result } = await renderHook(() => useAssistReview());

    await act(() => result.current.start(DRAFT));

    expect(useSession.getState().token).toBeNull();
  });

  it('reports a stream that ends without a result', async () => {
    FETCH.mockResolvedValue(streamed([frame({ type: 'feedback_delta', text: 'Say' })]));
    const { result } = await renderHook(() => useAssistReview());

    await act(() => result.current.start(DRAFT));

    expect(result.current.status).toBe('error');
    expect(result.current.error).toMatch(/stopped before it finished/);
  });

  it('cancel aborts the request and resets the state', async () => {
    let signal: AbortSignal | undefined;
    FETCH.mockImplementation(
      (_url: string, init: { signal: AbortSignal }) =>
        new Promise((_resolve, reject) => {
          signal = init.signal;
          init.signal.addEventListener('abort', () => reject(new Error('aborted')));
        }),
    );
    const { result } = await renderHook(() => useAssistReview());

    let running: Promise<void> = Promise.resolve();
    await act(async () => {
      running = result.current.start(DRAFT);
    });
    expect(result.current.status).toBe('streaming');
    await act(async () => {
      result.current.cancel();
      await running;
    });

    expect(signal?.aborted).toBe(true);
    expect(result.current.status).toBe('idle');
  });
});
