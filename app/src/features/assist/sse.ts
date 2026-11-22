import type { AssistEvent, AssistFailed } from './types';

const INVALID: AssistFailed = {
  type: 'error',
  code: 'invalid_event',
  message: 'The review could not be read.',
};
const TYPES = new Set(['feedback_delta', 'done', 'error']);

/**
 * Splits a server-sent event stream into events.
 *
 * Chunks from the network can end mid-event, so the unfinished tail comes back
 * as `rest`, to be prepended to the next chunk. Each event's `data:` lines hold
 * one JSON `AssistEvent`; anything unreadable becomes an error event.
 */
export function parseEvents(buffer: string): { events: AssistEvent[]; rest: string } {
  const frames = buffer.replaceAll('\r\n', '\n').split('\n\n');
  // The last piece has no blank line after it yet: it is incomplete.
  const rest = frames.pop() ?? '';
  const events: AssistEvent[] = [];
  for (const frame of frames) {
    const data = frame
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice('data:'.length).replace(/^ /, ''));
    // Comments and keep-alive frames carry no data.
    if (data.length === 0) continue;
    events.push(toEvent(data.join('\n')));
  }
  return { events, rest };
}

function toEvent(data: string): AssistEvent {
  try {
    const value: unknown = JSON.parse(data);
    if (
      typeof value === 'object' &&
      value !== null &&
      'type' in value &&
      TYPES.has(String(value.type))
    ) {
      return value as AssistEvent;
    }
  } catch {
    // Malformed JSON falls through to the error event.
  }
  return INVALID;
}
