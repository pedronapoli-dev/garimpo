import { parseEvents } from './sse';

const delta = (text: string) => `data: ${JSON.stringify({ type: 'feedback_delta', text })}\n\n`;

describe('parseEvents', () => {
  it('reads one complete event', () => {
    expect(parseEvents(delta('Say'))).toEqual({
      events: [{ type: 'feedback_delta', text: 'Say' }],
      rest: '',
    });
  });

  it('reads several events from one chunk', () => {
    const { events } = parseEvents(delta('Say ') + delta('why.'));

    expect(events.map((event) => event.type === 'feedback_delta' && event.text)).toEqual([
      'Say ',
      'why.',
    ]);
  });

  it('keeps an incomplete event for the next chunk', () => {
    const full = delta('Say');
    const first = parseEvents(full.slice(0, 10));

    expect(first).toEqual({ events: [], rest: full.slice(0, 10) });
    expect(parseEvents(first.rest + full.slice(10)).events).toHaveLength(1);
  });

  it('accepts CRLF line endings', () => {
    expect(parseEvents(delta('Say').replaceAll('\n', '\r\n')).events).toHaveLength(1);
  });

  it('ignores comments, keep-alive lines and other fields', () => {
    const chunk = `: ping\n\nevent: message\nid: 1\n${delta('Say')}`;

    expect(parseEvents(chunk).events).toEqual([{ type: 'feedback_delta', text: 'Say' }]);
  });

  it('joins a payload split over several data lines', () => {
    const chunk = 'data: {"type": "feedback_delta",\ndata: "text": "Say"}\n\n';

    expect(parseEvents(chunk).events).toEqual([{ type: 'feedback_delta', text: 'Say' }]);
  });

  it.each([
    ['malformed JSON', 'data: {not json\n\n'],
    ['an unknown event type', 'data: {"type": "other"}\n\n'],
    ['a payload that is not an object', 'data: 42\n\n'],
  ])('turns %s into an error event', (_, chunk) => {
    expect(parseEvents(chunk).events).toEqual([
      { type: 'error', code: 'invalid_event', message: 'The review could not be read.' },
    ]);
  });
});
