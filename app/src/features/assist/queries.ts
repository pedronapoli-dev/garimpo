import { useQuery } from '@tanstack/react-query';
import { fetch } from 'expo/fetch';
import { useCallback, useEffect, useRef, useState } from 'react';

import { API_URL, client } from '@/api/client';
import { ApiError, type ErrorOut, errorMessage, unwrap } from '@/api/errors';
import { useSession } from '@/stores/session';

import { parseEvents } from './sse';
import type { AssistEvent, AssistIn, AssistResult } from './types';

export const assistKeys = {
  status: ['assist', 'status'] as const,
};

/** Whether the server has a curator assist. Without one, the editor hides it. */
export function useAssistStatus() {
  return useQuery({
    queryKey: assistKeys.status,
    queryFn: async () => unwrap(await client.GET('/assist/status')),
    // The server's configuration does not change while the app runs.
    staleTime: Infinity,
  });
}

export type ReviewState = {
  status: 'idle' | 'streaming' | 'done' | 'error';
  feedback: string;
  result: AssistResult | null;
  error: string | null;
};

const IDLE: ReviewState = { status: 'idle', feedback: '', result: null, error: null };

export function applyEvent(state: ReviewState, event: AssistEvent): ReviewState {
  switch (event.type) {
    case 'feedback_delta':
      return { ...state, feedback: state.feedback + event.text };
    case 'done':
      return { ...state, status: 'done', result: event.result, feedback: event.result.feedback };
    case 'error':
      return { ...state, status: 'error', error: event.message };
  }
}

/**
 * Streams a review of the draft. openapi-fetch cannot read a body as a stream,
 * so this one request uses `fetch` from expo/fetch, the way URLSession.bytes
 * reads a response line by line in Swift.
 */
export function useAssistReview() {
  const [state, setState] = useState<ReviewState>(IDLE);
  const controller = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    controller.current?.abort();
    controller.current = null;
  }, []);

  // Leaving the screen stops the stream.
  useEffect(() => cancel, [cancel]);

  const start = useCallback(
    async (draft: AssistIn) => {
      cancel();
      const current = new AbortController();
      controller.current = current;
      setState({ ...IDLE, status: 'streaming' });
      try {
        await streamReview(draft, current.signal, (event) =>
          setState((previous) => applyEvent(previous, event)),
        );
        // A stream that ends without done or error leaves nothing to show.
        setState((previous) =>
          previous.status === 'streaming'
            ? { ...previous, status: 'error', error: INCOMPLETE }
            : previous,
        );
      } catch (error) {
        if (current.signal.aborted) {
          setState(IDLE);
          return;
        }
        setState((previous) => ({ ...previous, status: 'error', error: errorMessage(error) }));
      } finally {
        if (controller.current === current) controller.current = null;
      }
    },
    [cancel],
  );

  return { ...state, start, cancel };
}

const INCOMPLETE = 'The review stopped before it finished. Try again.';
const UNKNOWN_ERROR = { code: 'unknown_error', message: 'Something went wrong. Try again.' };

function isErrorOut(value: unknown): value is ErrorOut {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as ErrorOut).code === 'string' &&
    typeof (value as ErrorOut).message === 'string'
  );
}

async function streamReview(
  draft: AssistIn,
  signal: AbortSignal,
  onEvent: (event: AssistEvent) => void,
): Promise<void> {
  const { token, signOut } = useSession.getState();
  const response = await fetch(`${API_URL}/assist/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token !== null ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(draft),
    signal,
  });
  if (!response.ok) {
    // Same rule as the client middleware: a rejected token signs out.
    if (response.status === 401 && token !== null) await signOut();
    const body: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, isErrorOut(body) ? body : UNKNOWN_ERROR);
  }
  if (response.body === null) throw new Error('The response has no body.');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseEvents(buffer);
    buffer = parsed.rest;
    parsed.events.forEach(onEvent);
  }
}
